from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from operations.models import (
    County,
    OperatorRoute,
    OperatorServicePoint,
    Parcel,
    Town,
    TransportOperator,
)


MAKOS_ROUTES = [
    ("Mumias", "Kakamega", "Mombasa"),
    ("Mombasa", "Mombasa", "Nairobi"),
    ("Nairobi", "Nairobi", "Kisumu"),
    ("Nakuru", "Nakuru", "Eldoret"),
    ("Nairobi", "Nairobi", "Malindi"),
    ("Nairobi", "Nairobi", "Kilifi"),
    ("Nairobi", "Nairobi", "Mtwapa"),
    ("Bomet", "Bomet", "Nairobi"),
    ("Bungoma", "Bungoma", "Mombasa"),
    ("Busia", "Busia", "Mombasa"),
    ("Busia", "Busia", "Nairobi"),
    ("Eldoret", "Uasin Gishu", "Mombasa"),
    ("Kakamega", "Kakamega", "Mombasa"),
    ("Keroka", "Kisii", "Mombasa"),
    ("Nairobi", "Nairobi", "Mombasa"),
    ("Nairobi", "Nairobi", "Diani"),
    ("Mombasa", "Mombasa", "Lamu"),
    ("Nairobi", "Nairobi", "Nakuru"),
]

DESTINATION_COUNTIES = {
    "Mombasa": "Mombasa",
    "Nairobi": "Nairobi",
    "Kisumu": "Kisumu",
    "Eldoret": "Uasin Gishu",
    "Malindi": "Kilifi",
    "Kilifi": "Kilifi",
    "Mtwapa": "Kilifi",
    "Bomet": "Bomet",
    "Bungoma": "Bungoma",
    "Busia": "Busia",
    "Diani": "Kwale",
    "Lamu": "Lamu",
    "Nakuru": "Nakuru",
}


def get_town(name, county_name):
    county = County.objects.get(name=county_name)
    town, _ = Town.objects.get_or_create(county=county, name=name)
    return town


class Command(BaseCommand):
    help = "Configure MAKOS SACCO as the only transport operator in the system."

    @transaction.atomic
    def handle(self, *args, **options):
        # Preserve parcel records and tracking numbers, but remove references to
        # legacy third-party routes/service points before deleting those records.
        other_operator_routes = OperatorRoute.objects.exclude(operator__name="MAKOS SACCO")
        other_service_points = OperatorServicePoint.objects.exclude(operator__name="MAKOS SACCO")

        Parcel.objects.filter(operator_route__in=other_operator_routes).update(operator_route=None)
        Parcel.objects.filter(operator_service_point__in=other_service_points).update(
            operator_service_point=None
        )

        other_service_points.delete()
        other_operator_routes.delete()
        TransportOperator.objects.exclude(name="MAKOS SACCO").delete()

        makos, _ = TransportOperator.objects.update_or_create(
            name="MAKOS SACCO",
            defaults={
                "category": TransportOperator.Category.PASSENGER,
                "website": "",
                "parcel_service_confirmed": True,
                "is_active": True,
                "notes": (
                    "The sole operator in this system. MAKOS SACCO manages parcel "
                    "registration, routing, branches, dispatch, delivery and tracking. "
                    "The configured route list must be confirmed operationally by MAKOS."
                ),
            },
        )

        route_count = 0
        for origin_name, origin_county, destination_name in MAKOS_ROUTES:
            origin = get_town(origin_name, origin_county)
            destination = get_town(
                destination_name,
                DESTINATION_COUNTIES[destination_name],
            )
            OperatorRoute.objects.update_or_create(
                operator=makos,
                origin=origin,
                destination=destination,
                defaults={
                    "service_type": TransportOperator.Category.PASSENGER,
                    "verification_status": OperatorRoute.Verification.CONFIRMED,
                    "source_url": "",
                    "last_verified": date.today(),
                    "parcel_service_confirmed": True,
                    "is_active": True,
                    "notes": (
                        "Configured as a MAKOS SACCO internal route using the "
                        "administrator-requested route list. Confirm actual service "
                        "availability before dispatch."
                    ),
                },
            )
            route_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"MAKOS SACCO is the only operator. Processed {route_count} route entries; "
                "legacy third-party operators, routes and service points were removed."
            )
        )
