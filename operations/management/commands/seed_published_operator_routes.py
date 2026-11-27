from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from operations.models import County, OperatorRoute, OperatorServicePoint, Town, TransportOperator


TAHMEED_ROUTES = [
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
]
MODERN_COAST_ROUTES = [
    ("Nairobi", "Nairobi", "Mombasa"),
    ("Nairobi", "Nairobi", "Malindi"),
    ("Nairobi", "Nairobi", "Diani"),
    ("Mombasa", "Mombasa", "Lamu"),
    ("Nairobi", "Nairobi", "Kisumu"),
    ("Nairobi", "Nairobi", "Nakuru"),
]


def get_town(name, county_name):
    county = County.objects.get(name=county_name)
    town, _ = Town.objects.get_or_create(county=county, name=name)
    return town


class Command(BaseCommand):
    help = "Seed operator-published passenger routes; this does not enable parcel dispatch."

    @transaction.atomic
    def handle(self, *args, **options):
        definitions = [
            ("Tahmeed Coach", "https://tahmeedcoach.co.ke/", TAHMEED_ROUTES),
            ("Modern Coast", "https://moderncoast.co.ke/", MODERN_COAST_ROUTES),
        ]
        # Fargo Courier's own branch directory publishes these towns/outlets.
        # Reconfirm the selected outlet before handing over a parcel.
        fargo, _ = TransportOperator.objects.update_or_create(
            name="Fargo Courier",
            defaults={
                "category": TransportOperator.Category.COURIER,
                "website": "https://www.fargocourier.co.ke/our-branches/",
                "parcel_service_confirmed": True,
                "is_active": True,
                "notes": "Courier operator; service points below are taken from its published branch directory. Confirm opening and acceptance at the selected outlet before dispatch.",
            },
        )
        fargo_points = [
            ("Limuru", "Kiambu"), ("Kitengela", "Kajiado"),
            ("Ruiru", "Kiambu"), ("Thika", "Kiambu"),
            ("Juja", "Kiambu"), ("Nairobi", "Nairobi"),
            ("Ngong", "Kajiado"), ("Ongata Rongai", "Kajiado"),
        ]
        for town_name, county_name in fargo_points:
            town = get_town(town_name, county_name)
            OperatorServicePoint.objects.update_or_create(
                operator=fargo, town=town,
                defaults={
                    "source_url": "https://www.fargocourier.co.ke/our-branches/",
                    "last_verified": date(2026, 11, 27),
                    "is_verified": True,
                    "accepts_parcels": True,
                    "is_active": True,
                    "address": "See operator branch directory for exact outlet address.",
                },
            )

        # Historical G4S stations are not automatically treated as current.
        TransportOperator.objects.update_or_create(
            name="G4S",
            defaults={
                "category": TransportOperator.Category.COURIER,
                "website": "https://www.g4s.com/",
                "parcel_service_confirmed": False,
                "is_active": True,
                "notes": "Historical station coverage is available in the CA 2022 baseline survey. Current parcel acceptance and branches require direct verification.",
            },
        )

        route_count = 0
        for name, website, routes in definitions:
            operator, _ = TransportOperator.objects.update_or_create(
                name=name,
                defaults={
                    "category": TransportOperator.Category.PASSENGER,
                    "website": website,
                    "parcel_service_confirmed": False,
                    "is_active": True,
                    "notes": "Passenger routes published on operator website. Parcel/cargo acceptance is not confirmed; do not use for parcel dispatch.",
                },
            )
            for origin_name, origin_county, destination_name in routes:
                # A route is published passenger information, not proof of parcel service.
                if name == "Tahmeed Coach" and origin_name == "Mumias":
                    origin_county = "Kakamega"
                origin = get_town(origin_name, origin_county)
                destination_county = {
                    "Kakamega": "Kakamega", "Nairobi": "Nairobi", "Kisumu": "Kisumu",
                    "Eldoret": "Uasin Gishu", "Malindi": "Kilifi", "Kilifi": "Kilifi",
                    "Mtwapa": "Kilifi", "Bomet": "Bomet", "Bungoma": "Bungoma",
                    "Busia": "Busia", "Mombasa": "Mombasa", "Diani": "Kwale",
                    "Lamu": "Lamu", "Nakuru": "Nakuru",
                }[destination_name]
                destination = get_town(destination_name, destination_county)
                OperatorRoute.objects.update_or_create(
                    operator=operator, origin=origin, destination=destination,
                    defaults={
                        "service_type": TransportOperator.Category.PASSENGER,
                        "verification_status": OperatorRoute.Verification.PUBLISHED,
                        "source_url": website,
                        "last_verified": date(2026, 11, 27),
                        "parcel_service_confirmed": False,
                        "is_active": True,
                        "notes": "Published passenger route only. No parcel service, timetable, fare, or intermediate stop is asserted.",
                    },
                )
                route_count += 1
        self.stdout.write(self.style.SUCCESS(
            f"Seeded/updated {route_count} operator-published passenger route records. "
            "Parcel acceptance remains disabled."
        ))
