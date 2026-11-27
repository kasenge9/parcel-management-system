import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("operations", "0003_kenya_destinations_and_routes")]

    operations = [
        migrations.AlterField(
            model_name="parcel",
            name="destination",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="destination_parcels", to="operations.branch",
            ),
        ),
        migrations.AddField(
            model_name="parcel",
            name="destination_town",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="destination_parcels", to="operations.town",
            ),
        ),
        migrations.AddField(
            model_name="parcel",
            name="operator_route",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="parcels", to="operations.operatorroute",
            ),
        ),
    ]
