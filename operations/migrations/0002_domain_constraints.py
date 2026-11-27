from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dispatchitem",
            name="dispatch",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="dispatch_items",
                to="operations.dispatch",
            ),
        ),
        migrations.AlterField(
            model_name="dispatchitem",
            name="parcel",
            field=models.ForeignKey(
                on_delete=models.PROTECT,
                related_name="dispatch_items",
                to="operations.parcel",
            ),
        ),
        migrations.AddConstraint(
            model_name="parcel",
            constraint=models.CheckConstraint(
                condition=Q(weight_kg__gt=0),
                name="parcel_weight_gt_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="parcel",
            constraint=models.CheckConstraint(
                condition=Q(delivery_fee__gte=0),
                name="parcel_fee_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="payment_amount_gt_zero",
            ),
        ),
        migrations.AddConstraint(
            model_name="dispatch",
            constraint=models.CheckConstraint(
                condition=Q(arrived_at__isnull=True)
                | Q(arrived_at__gte=F("departure_time")),
                name="dispatch_arrival_after_depart",
            ),
        ),
    ]
