from django.core.management.base import BaseCommand
from django.db import transaction

from operations.models import County, Town


# County headquarters plus selected established towns/localities for destination search.
COUNTY_TOWNS = [
    (1, "Mombasa", ["Mombasa", "Likoni", "Bamburi", "Kisauni", "Mtwapa"]),
    (2, "Kwale", ["Kwale", "Ukunda", "Diani", "Msambweni", "Lunga Lunga"]),
    (3, "Kilifi", ["Kilifi", "Malindi", "Watamu", "Mariakani", "Kilifi South"]),
    (4, "Tana River", ["Hola", "Garsen", "Bura", "Madogo"]),
    (5, "Lamu", ["Lamu", "Mpeketoni", "Witu", "Faza"]),
    (6, "Taita-Taveta", ["Mwatate", "Voi", "Wundanyi", "Taveta"]),
    (7, "Garissa", ["Garissa", "Dadaab", "Masalani", "Ijara"]),
    (8, "Wajir", ["Wajir", "Habaswein", "Griftu", "Buna"]),
    (9, "Mandera", ["Mandera", "El Wak", "Rhamu", "Takaba"]),
    (10, "Marsabit", ["Marsabit", "Moyale", "Laisamis", "North Horr"]),
    (11, "Isiolo", ["Isiolo", "Merti", "Garbatulla"]),
    (12, "Meru", ["Meru", "Maua", "Nkubu", "Timau", "Laare"]),
    (13, "Tharaka-Nithi", ["Kathwana", "Chuka", "Marimanti", "Chiakariga"]),
    (14, "Embu", ["Embu", "Runyenjes", "Siakago", "Manyatta"]),
    (15, "Kitui", ["Kitui", "Mwingi", "Mutomo", "Kyuso"]),
    (16, "Machakos", ["Machakos", "Athi River", "Kangundo", "Tala", "Matuu"]),
    (17, "Makueni", ["Wote", "Makindu", "Kibwezi", "Mtito Andei", "Emali"]),
    (18, "Nyandarua", ["Ol Kalou", "Engineer", "Njabini", "Ndaragwa"]),
    (19, "Nyeri", ["Nyeri", "Karatina", "Othaya", "Mukurweini"]),
    (20, "Kirinyaga", ["Kerugoya", "Kutus", "Wanguru", "Sagana"]),
    (21, "Murang'a", ["Murang'a", "Kenol", "Maragua", "Kangema", "Kiriaini"]),
    (22, "Kiambu", ["Kiambu", "Thika", "Ruiru", "Limuru", "Kikuyu", "Juja", "Githunguri"]),
    (23, "Turkana", ["Lodwar", "Kakuma", "Lokichar", "Lokitaung"]),
    (24, "West Pokot", ["Kapenguria", "Kacheliba", "Chepareria", "Ortum"]),
    (25, "Samburu", ["Maralal", "Baragoi", "Wamba", "Archers Post"]),
    (26, "Trans Nzoia", ["Kitale", "Kiminini", "Endebess", "Kachibora"]),
    (27, "Uasin Gishu", ["Eldoret", "Burnt Forest", "Turbo", "Moi's Bridge"]),
    (28, "Elgeyo-Marakwet", ["Iten", "Kapsowar", "Tambach", "Chebiemit"]),
    (29, "Nandi", ["Kapsabet", "Nandi Hills", "Mosoriot", "Kabiyet"]),
    (30, "Baringo", ["Kabarnet", "Eldama Ravine", "Marigat", "Mogotio"]),
    (31, "Laikipia", ["Nanyuki", "Nyahururu", "Rumuruti", "Doldol"]),
    (32, "Nakuru", ["Nakuru", "Naivasha", "Gilgil", "Molo", "Njoro", "Mai Mahiu"]),
    (33, "Narok", ["Narok", "Kilgoris", "Ololulunga", "Suswa"]),
    (34, "Kajiado", ["Kajiado", "Kitengela", "Ngong", "Ongata Rongai", "Loitokitok"]),
    (35, "Kericho", ["Kericho", "Litein", "Londiani", "Kipkelion"]),
    (36, "Bomet", ["Bomet", "Sotik", "Longisa", "Mulot"]),
    (37, "Kakamega", ["Kakamega", "Mumias", "Malava", "Butere", "Shinyalu"]),
    (38, "Vihiga", ["Mbale", "Luanda", "Chavakali", "Hamisi"]),
    (39, "Bungoma", ["Bungoma", "Webuye", "Kimilili", "Chwele", "Malaba"]),
    (40, "Busia", ["Busia", "Malaba", "Nambale", "Port Victoria", "Funyula"]),
    (41, "Siaya", ["Siaya", "Bondo", "Ugunja", "Yala", "Usenge"]),
    (42, "Kisumu", ["Kisumu", "Ahero", "Muhoroni", "Maseno", "Katito"]),
    (43, "Homa Bay", ["Homa Bay", "Oyugis", "Mbita", "Kendu Bay", "Ndhiwa"]),
    (44, "Migori", ["Migori", "Rongo", "Awendo", "Kehancha", "Isebania"]),
    (45, "Kisii", ["Kisii", "Ogembo", "Suneka", "Keroka"]),
    (46, "Nyamira", ["Nyamira", "Keroka", "Nyansiongo", "Ekerenyo"]),
    (47, "Nairobi", ["Nairobi", "Westlands", "Karen", "Kasarani", "Embakasi", "Kibera"]),
]


class Command(BaseCommand):
    help = "Idempotently seed Kenya's 47 counties and a starter list of towns."

    @transaction.atomic
    def handle(self, *args, **options):
        created_counties = created_towns = 0
        for code, county_name, town_names in COUNTY_TOWNS:
            county, created = County.objects.update_or_create(
                code=code, defaults={"name": county_name}
            )
            created_counties += int(created)
            for town_name in town_names:
                _, created = Town.objects.get_or_create(county=county, name=town_name)
                created_towns += int(created)
        self.stdout.write(self.style.SUCCESS(
            f"Kenya destination seed complete: {County.objects.count()} counties, "
            f"{Town.objects.count()} towns ({created_counties} counties and "
            f"{created_towns} towns newly created)."
        ))
