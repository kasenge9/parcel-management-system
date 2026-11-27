from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from operations.models import (
    County,
    OperatorRoute,
    OperatorServicePoint,
    Town,
    TransportOperator,
)


# Retains the same 20 origin/destination entries previously loaded from the
# Tahmeed and Modern Coast lists, now configured under MAKOS SACCO as requested.
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
    help = "Seed MAKOS SACCO and its configured parcel routes; deactivate other operators."

    @transaction.atomic
    def handle(self, *args, **options):
        # Keep historical records for audit purposes, but prevent any other
        # operator, route, or service point from being offered for new parcels.
        TransportOperator.objects.exclude(name="MAKOS SACCO").update(is_active=False)
        OperatorRoute.objects.exclude(operator__name="MAKOS SACCO").update(
            is_active=False,
            parcel_service_confirmed=False,
        )
        OperatorServicePoint.objects.exclude(operator__name="MAKOS SACCO").update(
            is_active=False,
            accepts_parcels=False,
        )

        makos, _ = TransportOperator.objects.update_or_create(
            name="MAKOS SACCO",
            defaults={
                "category": TransportOperator.Category.PASSENGER,
                "website": "",
                "parcel_service_confirmed": True,
                "is_active": True,
                "notes": (
                    "Sole transport operator configured for this parcel management system. "
                    "Routes use the same origin/destination list requested by the administrator. "
                    "Confirm operational service and parcel handling with MAKOS before dispatch."
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
                        "Configured under MAKOS SACCO using the administrator-requested "
                        "route list. Confirm actual service availability before dispatch."
                    ),
                },
            )
            route_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"MAKOS SACCO configured. Processed {route_count} route entries. "
                "All other operators and their routes/service points are inactive."
            )
        )
