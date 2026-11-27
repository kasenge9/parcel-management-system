import secrets
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Branch(models.Model):
    """A physical SACCO location that accepts or dispatches parcels."""

    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=180)
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
        Branch, on_delete=models.PROTECT, related_name="destination_parcels"
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
                name="parcel_delivery_fee_nonnegative",
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
        if errors:
            raise ValidationError(errors)

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
                name="dispatch_arrival_after_departure",
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
