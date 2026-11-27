from django.contrib import admin
from .models import (
    Branch, County, Customer, Dispatch, DispatchItem, Driver, OperatorRoute,
    OperatorServicePoint, Parcel, Payment, RouteStop, Town, TrackingEvent,
    TransportOperator, Vehicle,
)


@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("name",)
    ordering = ("code",)


@admin.register(Town)
class TownAdmin(admin.ModelAdmin):
    list_display = ("name", "county")
    list_filter = ("county",)
    search_fields = ("name", "county__name")
    autocomplete_fields = ("county",)


@admin.register(TransportOperator)
class TransportOperatorAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "parcel_service_confirmed", "is_active")
    list_filter = ("category", "parcel_service_confirmed", "is_active")
    search_fields = ("name",)


@admin.register(OperatorServicePoint)
class OperatorServicePointAdmin(admin.ModelAdmin):
    list_display = ("operator", "town", "is_verified", "accepts_parcels", "is_active", "last_verified")
    list_filter = ("operator", "is_verified", "accepts_parcels", "is_active", "town__county")
    search_fields = ("operator__name", "town__name", "address")
    autocomplete_fields = ("operator", "town")


class RouteStopInline(admin.TabularInline):
    model = RouteStop
    extra = 0
    autocomplete_fields = ("town",)


@admin.register(OperatorRoute)
class OperatorRouteAdmin(admin.ModelAdmin):
    list_display = ("operator", "origin", "destination", "service_type", "verification_status", "parcel_service_confirmed", "is_active")
    list_filter = ("operator", "service_type", "verification_status", "parcel_service_confirmed", "is_active")
    search_fields = ("operator__name", "origin__name", "destination__name")
    autocomplete_fields = ("operator", "origin", "destination")
    inlines = (RouteStopInline,)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "town", "phone", "is_active")
    list_filter = ("is_active", "town__county")
    search_fields = ("name", "location", "town__name")
    autocomplete_fields = ("town",)


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ("tracking_number", "sender", "recipient", "origin", "destination_town", "operator_route", "route_assignment_status", "status", "created_at")
    list_filter = ("status", "origin", "destination_town", "created_at")
    search_fields = ("tracking_number", "sender__full_name", "recipient__full_name", "sender__phone", "recipient__phone")
    readonly_fields = ("tracking_number", "created_at", "updated_at")
    autocomplete_fields = ("destination_town", "operator_route")


admin.site.register([Customer, TrackingEvent, Payment, Vehicle, Driver, Dispatch, DispatchItem])
