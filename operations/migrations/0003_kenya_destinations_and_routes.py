# Generated for Kenya destination and operator route directory.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("operations", "0002_domain_constraints")]

    operations = [
        migrations.CreateModel(
            name="County",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("code", models.PositiveSmallIntegerField(unique=True)),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="Town",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("county", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="towns", to="operations.county")),
            ],
            options={"ordering": ["county__code", "name"]},
        ),
        migrations.CreateModel(
            name="TransportOperator",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("category", models.CharField(choices=[("courier", "Courier"), ("passenger", "Passenger transport"), ("freight", "Freight / logistics")], max_length=20)),
                ("name", models.CharField(max_length=160, unique=True)),
                ("website", models.URLField(blank=True)),
                ("parcel_service_confirmed", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="OperatorServicePoint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("address", models.CharField(blank=True, max_length=240)),
                ("phone", models.CharField(blank=True, max_length=40)),
                ("source_url", models.URLField(blank=True)),
                ("last_verified", models.DateField(blank=True, null=True)),
                ("is_verified", models.BooleanField(default=False)),
                ("accepts_parcels", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=False)),
                ("operator", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="service_points", to="operations.transportoperator")),
                ("town", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operator_service_points", to="operations.town")),
            ],
            options={"ordering": ["operator__name", "town__name"]},
        ),
        migrations.CreateModel(
            name="OperatorRoute",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("service_type", models.CharField(choices=[("courier", "Courier"), ("passenger", "Passenger transport"), ("freight", "Freight / logistics")], max_length=20)),
                ("verification_status", models.CharField(choices=[("unverified", "Unverified"), ("published", "Published by operator"), ("confirmed", "Confirmed directly with operator")], default="unverified", max_length=20)),
                ("source_url", models.URLField(blank=True)),
                ("last_verified", models.DateField(blank=True, null=True)),
                ("parcel_service_confirmed", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True)),
                ("destination", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="routes_to", to="operations.town")),
                ("operator", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="routes", to="operations.transportoperator")),
                ("origin", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="routes_from", to="operations.town")),
            ],
            options={"ordering": ["operator__name", "origin__name", "destination__name"]},
        ),
        migrations.CreateModel(
            name="RouteStop",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sequence", models.PositiveSmallIntegerField()),
                ("route", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="stops", to="operations.operatorroute")),
                ("town", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="route_stops", to="operations.town")),
            ],
            options={"ordering": ["sequence"]},
        ),
        migrations.AddField(
            model_name="branch",
            name="town",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="sacco_branches", to="operations.town"),
        ),
        migrations.AddConstraint(model_name="town", constraint=models.UniqueConstraint(fields=("county", "name"), name="unique_town_per_county")),
        migrations.AddConstraint(model_name="operatorservicepoint", constraint=models.UniqueConstraint(fields=("operator", "town"), name="unique_operator_service_town")),
        migrations.AddConstraint(model_name="operatorroute", constraint=models.UniqueConstraint(fields=("operator", "origin", "destination"), name="unique_operator_route")),
        migrations.AddConstraint(model_name="routestop", constraint=models.UniqueConstraint(fields=("route", "sequence"), name="unique_route_stop_order")),
        migrations.AddConstraint(model_name="routestop", constraint=models.UniqueConstraint(fields=("route", "town"), name="unique_town_per_route")),
    ]
