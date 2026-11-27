from decimal import Decimal

from django.test import TestCase

from .forms import ParcelForm
from .models import Branch
from .pricing import calculate_delivery_fee, get_parcel_category


class ParcelPricingTests(TestCase):
    def test_description_selects_expected_categories(self):
        self.assertEqual(get_parcel_category("Two signed documents"), "documents")
        self.assertEqual(get_parcel_category("Laptop and charger"), "electronics")
        self.assertEqual(get_parcel_category("Fragile glass bottle"), "fragile")
        self.assertEqual(get_parcel_category("Books and household items"), "general")

    def test_fee_uses_category_and_weight(self):
        self.assertEqual(calculate_delivery_fee("documents", Decimal("2.00")), Decimal("150.00"))
        self.assertEqual(calculate_delivery_fee("laptop", Decimal("2.00")), Decimal("400.00"))

    def test_form_recalculates_fee_instead_of_trusting_posted_value(self):
        origin = Branch.objects.create(name="Nairobi", location="Nairobi")
        destination = Branch.objects.create(name="Kisumu", location="Kisumu")
        form = ParcelForm(data={
            "description": "documents",
            "weight_kg": "2.00",
            "origin": origin.pk,
            "destination": destination.pk,
            "delivery_fee": "0.01",
            "sender_name": "Sender",
            "sender_phone": "0700000001",
            "recipient_name": "Recipient",
            "recipient_phone": "0700000002",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["delivery_fee"], Decimal("150.00"))
        self.assertTrue(form.fields["delivery_fee"].widget.attrs.get("readonly"))
