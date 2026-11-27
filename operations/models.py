import secrets
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone



class County(models.Model):
    """One of Kenya's 47 counties."""
    name = models.CharField(max_length=100, unique=True)
    code = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.name


class Town(models.Model):
    """A named town or destination within a Kenyan county."""
    county = models.ForeignKey(County, on_delete=models.PROTECT, related_name="towns")
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["county__code", "name"]
        constraints = [
            models.UniqueConstraint(fields=["county", "name"], name="unique_town_per_county")
        ]

    def __str__(self):
        return f"{self.name}, {self.county.name}"


class TransportOperator(models.Model):
    class Category(models.TextChoices):
        COURIER = "courier", "Courier"
        PASSENGER = "passenger", "Passenger transport"
        FREIGHT = "freight", "Freight / logistics"

    name = models.CharField(max_length=160, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    website = models.URLField(blank=True)
    parcel_service_confirmed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class OperatorServicePoint(models.Model):
    operator = models.ForeignKey(TransportOperator, on_delete=models.PROTECT, related_name="service_points")
    town = models.ForeignKey(Town, on_delete=models.PROTECT, related_name="operator_service_points")
    address = models.CharField(max_length=240, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    source_url = models.URLField(blank=True)
    last_verified = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    accepts_parcels = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["operator__name", "town__name"]
        constraints = [
            models.UniqueConstraint(fields=["operator", "town"], name="unique_operator_service_town")
        ]

    def clean(self):
        super().clean()
        if self.is_active and not self.is_verified:
            raise ValidationError({"is_active": "A service point must be verified before activation."})
        if self.accepts_parcels and not self.operator.parcel_service_confirmed:
            raise ValidationError({"accepts_parcels": "Confirm parcel service with the operator before enabling parcel acceptance."})

    def __str__(self):
        return f"{self.operator} — {self.town}"


class OperatorRoute(models.Model):
    class Verification(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified"
        PUBLISHED = "published", "Published by operator"
        CONFIRMED = "confirmed", "Confirmed directly with operator"

    operator = models.ForeignKey(TransportOperator, on_delete=models.PROTECT, related_name="routes")
    origin = models.ForeignKey(Town, on_delete=models.PROTECT, related_name="routes_from")
    destination = models.ForeignKey(Town, on_delete=models.PROTECT, related_name="routes_to")
    service_type = models.CharField(max_length=20, choices=TransportOperator.Category.choices)
    verification_status = models.CharField(max_length=20, choices=Verification.choices, default=Verification.UNVERIFIED)
    source_url = models.URLField(blank=True)
    last_verified = models.DateField(null=True, blank=True)
    parcel_service_confirmed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["operator__name", "origin__name", "destination__name"]
        constraints = [
            models.UniqueConstraint(fields=["operator", "origin", "destination"], name="unique_operator_route")
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.origin_id and self.destination_id and self.origin_id == self.destination_id:
            errors["destination"] = "Route destination must differ from its origin."
        if self.is_active and self.verification_status == self.Verification.UNVERIFIED:
            errors["is_active"] = "Verify a route before activating it."
        if self.parcel_service_confirmed and not self.operator.parcel_service_confirmed:
            errors["parcel_service_confirmed"] = "Confirm parcel service at operator level first."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.operator}: {self.origin} to {self.destination}"


class RouteStop(models.Model):
    route = models.ForeignKey(OperatorRoute, on_delete=models.CASCADE, related_name="stops")
    town = models.ForeignKey(Town, on_delete=models.PROTECT, related_name="route_stops")
    sequence = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["route", "sequence"], name="unique_route_stop_order"),
            models.UniqueConstraint(fields=["route", "town"], name="unique_town_per_route"),
        ]

    def __str__(self):
        return f"{self.sequence}. {self.town} ({self.route})"


class Branch(models.Model):
    """A physical SACCO location that accepts or dispatches parcels."""

    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=180)
    town = models.ForeignKey(Town, null=True, blank=True, on_delete=models.PROTECT, related_name="sacco_branches")
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        errors = {}
        if self.name is not None and not self.name.strip():
            errors["name"] = "Enter a branch name."
        if self.location is not None and not self.location.strip():
            errors["location"] = "Enter the branch location."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name


class Customer(models.Model):
    """A person recorded as a parcel sender or recipient."""

    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        errors = {}
        if self.full_name is not None and not self.full_name.strip():
            errors["full_name"] = "Enter the customer's full name."
        if self.phone is not None and not self.phone.strip():
            errors["phone"] = "Enter the customer's phone number."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.full_name} ({self.phone})"


class Parcel(models.Model):
    """A registered consignment with a stable, publicly searchable code."""

    class Status(models.TextChoices):
        REGISTERED = "registered", "Registered"
        PAYMENT_PENDING = "payment_pending", "Payment pending"
        PAID = "paid", "Paid"
        READY_DISPATCH = "ready_dispatch", "Ready for dispatch"
        IN_TRANSIT = "in_transit", "In transit"
        ARRIVED = "arrived", "Arrived at destination"
        READY_COLLECTION = "ready_collection", "Ready for collection"
        COLLECTED = "collected", "Collected"
        RETURNED = "returned", "Returned"
        CANCELLED = "cancelled", "Cancelled"

    tracking_number = models.CharField(
        max_length=16, unique=True, editable=False, db_index=True
    )
    sender = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="sent_parcels"
    )
    recipient = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="received_parcels"
    )
    description = models.CharField(max_length=240)
    weight_kg = models.DecimalField(max_digits=7, decimal_places=2)
    origin = models.ForeignKey(
        Branch, on_delete=models.PROTECT, related_name="origin_parcels"
    )
    destination = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT,
        related_name="destination_parcels"
    )
    destination_town = models.ForeignKey(
        Town, null=True, blank=True, on_delete=models.PROTECT,
        related_name="destination_parcels"
    )
    operator_route = models.ForeignKey(
        OperatorRoute, null=True, blank=True, on_delete=models.PROTECT,
        related_name="parcels"
    )
    operator_service_point = models.ForeignKey(
        OperatorServicePoint, null=True, blank=True, on_delete=models.PROTECT,
        related_name="parcels"
    )
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.REGISTERED
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(weight_kg__gt=0),
                name="parcel_weight_gt_zero",
            ),
            models.CheckConstraint(
                condition=Q(delivery_fee__gte=0),
                name="parcel_fee_nonnegative",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.description is not None and not self.description.strip():
            errors["description"] = "Enter a parcel description."
        if self.weight_kg is not None and self.weight_kg <= 0:
            errors["weight_kg"] = "Parcel weight must be greater than zero."
        if self.delivery_fee is not None and self.delivery_fee < 0:
            errors["delivery_fee"] = "Delivery fee cannot be negative."
        if self.operator_service_point_id:
            service_point = self.operator_service_point
            if (not service_point.is_active or not service_point.is_verified
                    or not service_point.accepts_parcels
                    or not service_point.operator.is_active
                    or not service_point.operator.parcel_service_confirmed):
                errors["operator_service_point"] = "Only active, verified service points accepting parcels can be assigned."
            if self.destination_town_id and service_point.town_id != self.destination_town_id:
                errors["operator_service_point"] = "The selected service point does not serve this destination town."
        if self.operator_route_id:
            route = self.operator_route
            if (not route.is_active or not route.parcel_service_confirmed
                    or not route.operator.is_active or not route.operator.parcel_service_confirmed
                    or route.verification_status == OperatorRoute.Verification.UNVERIFIED):
                errors["operator_route"] = "Only active, verified routes confirmed for parcel service can be assigned."
            if self.destination_town_id and route.destination_id != self.destination_town_id:
                errors["operator_route"] = "The selected route does not serve this destination town."
            if self.operator_service_point_id and self.operator_service_point.operator_id != route.operator_id:
                errors["operator_route"] = "The selected route and receiving service point must belong to the same operator."
            if self.origin_id and not self.origin.town_id:
                errors["operator_route"] = "Set the origin branch town before assigning an operator route."
            elif self.origin_id and route.origin_id != self.origin.town_id:
                errors["operator_route"] = "The selected route does not match the parcel origin branch town."
        if errors:
            raise ValidationError(errors)

    @property
    def route_assignment_status(self):
        return "assigned" if self.operator_route_id else "awaiting_route_assignment"

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            alphabet = string.ascii_uppercase + string.digits
            self.tracking_number = "MK" + "".join(
                secrets.choice(alphabet) for _ in range(10)
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tracking_number


class TrackingEvent(models.Model):
    """An immutable-style status/location entry in a parcel's history."""

    parcel = models.ForeignKey(
        Parcel, on_delete=models.CASCADE, related_name="tracking_events"
    )
    status = models.CharField(max_length=24, choices=Parcel.Status.choices)
    location = models.CharField(max_length=180, blank=True)
    note = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.parcel.tracking_number}: {self.get_status_display()}"


class Payment(models.Model):
    """A recorded payment against a parcel; financial history is protected."""

    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        MOBILE_MONEY = "mobile_money", "Mobile money"
        OTHER = "other", "Other"

    parcel = models.ForeignKey(
        Parcel, on_delete=models.PROTECT, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    paid_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="payment_amount_gt_zero",
            ),
        ]

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Payment amount must be greater than zero."})

    def __str__(self):
        return f"{self.parcel.tracking_number} — {self.amount}"


class Vehicle(models.Model):
    """A vehicle available for branch-to-branch parcel dispatch."""

    registration_number = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        if self.registration_number is not None and not self.registration_number.strip():
            raise ValidationError(
                {"registration_number": "Enter the vehicle registration number."}
            )

    def __str__(self):
        return self.registration_number


class Driver(models.Model):
    """A driver assigned to a dispatch."""

    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        errors = {}
        if self.full_name is not None and not self.full_name.strip():
            errors["full_name"] = "Enter the driver's full name."
        if self.phone is not None and not self.phone.strip():
            errors["phone"] = "Enter the driver's phone number."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.full_name


class Dispatch(models.Model):
    """A vehicle and driver movement between two branches."""

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT, related_name="dispatches"
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.PROTECT, related_name="dispatches"
    )
    origin = models.ForeignKey(
        Branch, on_delete=models.PROTECT, related_name="departures"
    )
    destination = models.ForeignKey(
        Branch, on_delete=models.PROTECT, related_name="arrivals"
    )
    departure_time = models.DateTimeField(default=timezone.now)
    arrived_at = models.DateTimeField(null=True, blank=True)
    parcels = models.ManyToManyField(
        Parcel, through="DispatchItem", related_name="dispatches"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(arrived_at__isnull=True)
                | Q(arrived_at__gte=F("departure_time")),
                name="dispatch_arrival_after_depart",
            ),
        ]

    def clean(self):
        super().clean()
        if (
            self.arrived_at is not None
            and self.departure_time is not None
            and self.arrived_at < self.departure_time
        ):
            raise ValidationError(
                {"arrived_at": "Arrival time cannot be earlier than departure time."}
            )

    def __str__(self):
        return f"{self.origin} to {self.destination}"


class DispatchItem(models.Model):
    """Through-table preventing the same parcel being added twice to one trip."""

    dispatch = models.ForeignKey(
        Dispatch, on_delete=models.CASCADE, related_name="dispatch_items"
    )
    parcel = models.ForeignKey(
        Parcel, on_delete=models.PROTECT, related_name="dispatch_items"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["dispatch", "parcel"],
                name="unique_parcel_per_dispatch",
            ),
        ]

    def __str__(self):
        return f"{self.parcel.tracking_number} on dispatch {self.dispatch_id}"
