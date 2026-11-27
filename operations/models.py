import secrets
import string
from django.conf import settings
from django.db import models
from django.utils import timezone

class Branch(models.Model):
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=180)
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Customer(models.Model):
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.full_name} ({self.phone})"

class Parcel(models.Model):
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
    tracking_number = models.CharField(max_length=16, unique=True, editable=False, db_index=True)
    sender = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="sent_parcels")
    recipient = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="received_parcels")
    description = models.CharField(max_length=240)
    weight_kg = models.DecimalField(max_digits=7, decimal_places=2)
    origin = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="origin_parcels")
    destination = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="destination_parcels")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.REGISTERED)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if not self.tracking_number:
            alphabet = string.ascii_uppercase + string.digits
            self.tracking_number = "MK" + "".join(secrets.choice(alphabet) for _ in range(10))
        super().save(*args, **kwargs)
    def __str__(self): return self.tracking_number

class TrackingEvent(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name="tracking_events")
    status = models.CharField(max_length=24, choices=Parcel.Status.choices)
    location = models.CharField(max_length=180, blank=True)
    note = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.parcel.tracking_number}: {self.get_status_display()}"

class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        MOBILE_MONEY = "mobile_money", "Mobile money"
        OTHER = "other", "Other"
    parcel = models.ForeignKey(Parcel, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    paid_at = models.DateTimeField(default=timezone.now)
    def __str__(self): return f"{self.parcel.tracking_number} — {self.amount}"

class Vehicle(models.Model):
    registration_number = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.registration_number

class Driver(models.Model):
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.full_name

class Dispatch(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="dispatches")
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="dispatches")
    origin = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="departures")
    destination = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="arrivals")
    departure_time = models.DateTimeField(default=timezone.now)
    arrived_at = models.DateTimeField(null=True, blank=True)
    parcels = models.ManyToManyField(Parcel, through="DispatchItem", related_name="dispatches")
    def __str__(self): return f"{self.origin} to {self.destination}"

class DispatchItem(models.Model):
    dispatch = models.ForeignKey(Dispatch, on_delete=models.CASCADE)
    parcel = models.ForeignKey(Parcel, on_delete=models.PROTECT)
    added_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["dispatch", "parcel"], name="unique_parcel_per_dispatch")]
