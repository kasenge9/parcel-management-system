from decimal import Decimal, ROUND_HALF_UP
import json

from django import forms

from .models import Branch, Customer, Parcel
from .pricing import CATEGORY_KEYWORDS, PRICE_RULES, calculate_delivery_fee


class ParcelForm(forms.ModelForm):
    sender_name = forms.CharField(max_length=160, label="Sender name")
    sender_phone = forms.CharField(max_length=30, label="Sender phone")
    recipient_name = forms.CharField(max_length=160, label="Recipient name")
    recipient_phone = forms.CharField(max_length=30, label="Recipient phone")

    class Meta:
        model = Parcel
        fields = ["description", "weight_kg", "origin", "destination", "delivery_fee"]
        widgets = {
            "description": forms.TextInput(attrs={"placeholder": "Documents or parcel contents"}),
            "weight_kg": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "delivery_fee": forms.NumberInput(attrs={"min": "0", "step": "0.01", "readonly": "readonly"}),
        }
        labels = {"delivery_fee": "Estimated delivery fee (KES)"}
        help_texts = {
            "delivery_fee": "Calculated from the parcel description and weight. Staff should confirm the estimate before accepting payment."
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["origin"].queryset = Branch.objects.filter(is_active=True)
        self.fields["destination"].queryset = Branch.objects.filter(is_active=True)
        self.fields["delivery_fee"].widget.attrs["data-pricing-rules"] = json.dumps(
            {category: {key: str(value) for key, value in rule.items()} for category, rule in PRICE_RULES.items()}
        )
        self.fields["delivery_fee"].widget.attrs["data-category-keywords"] = json.dumps(CATEGORY_KEYWORDS)

    def clean_weight_kg(self):
        value = self.cleaned_data["weight_kg"]
        if value <= 0:
            raise forms.ValidationError("Weight must be greater than zero.")
        return value

    def clean_delivery_fee(self):
        # Never trust a fee submitted by the browser; recalculate on the server.
        description = self.cleaned_data.get("description", "")
        weight_kg = self.cleaned_data.get("weight_kg")
        if not description or weight_kg is None:
            return self.cleaned_data.get("delivery_fee")
        return calculate_delivery_fee(description, weight_kg)

    def save(self, commit=True):
        parcel = super().save(commit=False)
        sender, _ = Customer.objects.get_or_create(
            phone=self.cleaned_data["sender_phone"],
            defaults={"full_name": self.cleaned_data["sender_name"]},
        )
        recipient, _ = Customer.objects.get_or_create(
            phone=self.cleaned_data["recipient_phone"],
            defaults={"full_name": self.cleaned_data["recipient_name"]},
        )
        parcel.sender, parcel.recipient = sender, recipient
        parcel.delivery_fee = calculate_delivery_fee(parcel.description, parcel.weight_kg)
        if commit:
            parcel.save()
        return parcel
