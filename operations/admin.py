from django.contrib import admin
from .models import Branch, Customer, Dispatch, DispatchItem, Driver, Parcel, Payment, TrackingEvent, Vehicle

@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ("tracking_number", "sender", "recipient", "origin", "destination", "status", "created_at")
    list_filter = ("status", "origin", "destination", "created_at")
    search_fields = ("tracking_number", "sender__full_name", "recipient__full_name", "sender__phone", "recipient__phone")
    readonly_fields = ("tracking_number", "created_at", "updated_at")
admin.site.register([Branch, Customer, TrackingEvent, Payment, Vehicle, Driver, Dispatch, DispatchItem])
