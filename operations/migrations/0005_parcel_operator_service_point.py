import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("operations", "0004_parcel_destination_town_and_route")]

    operations = [
        migrations.AddField(
            model_name="parcel",
            name="operator_service_point",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="parcels", to="operations.operatorservicepoint",
            ),
        ),
    ]
