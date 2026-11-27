from django import forms

from .models import Branch, Customer, Parcel


class ParcelForm(forms.ModelForm):
    sender_name = forms.CharField(max_length=160, label="Sender name")
    sender_phone = forms.CharField(max_length=30, label="Sender phone")
    recipient_name = forms.CharField(max_length=160, label="Recipient name")
    recipient_phone = forms.CharField(max_length=30, label="Recipient phone")

    class Meta:
        model = Parcel
        fields = [
            "description",
            "weight_kg",
            "origin",
            "destination",
            "delivery_fee",
        ]
        widgets = {
            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Documents or parcel contents",
                    "maxlength": 240,
                }
            ),
            "weight_kg": forms.NumberInput(
                attrs={"class": "form-control", "min": "0.01", "step": "0.01"}
            ),
            "origin": forms.Select(attrs={"class": "form-select"}),
            "destination": forms.Select(attrs={"class": "form-select"}),
            "delivery_fee": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "0.01"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("sender_name", "recipient_name"):
            self.fields[name].widget.attrs.update(
                {"class": "form-control", "autocomplete": "name"}
            )
        for name in ("sender_phone", "recipient_phone"):
            self.fields[name].widget.attrs.update(
                {
                    "class": "form-control",
                    "autocomplete": "tel",
                    "inputmode": "tel",
                }
            )
        self.fields["origin"].queryset = Branch.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["destination"].queryset = Branch.objects.filter(
            is_active=True
        ).order_by("name")
        self.fields["description"].help_text = "Describe the parcel contents."
        self.fields["weight_kg"].help_text = "Enter a weight greater than zero."
        self.fields["delivery_fee"].help_text = "Amount in Kenyan shillings (KES)."

    def clean_weight_kg(self):
        value = self.cleaned_data["weight_kg"]
        if value <= 0:
            raise forms.ValidationError("Weight must be greater than zero.")
        return value

    def clean_delivery_fee(self):
        value = self.cleaned_data["delivery_fee"]
        if value < 0:
            raise forms.ValidationError("Delivery fee cannot be negative.")
        return value

    def clean_description(self):
        value = self.cleaned_data["description"].strip()
        if not value:
            raise forms.ValidationError("Enter a description of the parcel.")
        return value

    def _customer_for(self, phone_field, name_field):
        phone = self.cleaned_data[phone_field].strip()
        name = self.cleaned_data[name_field].strip()
        customer = Customer.objects.filter(phone=phone).order_by("pk").first()
        if customer is None:
            customer = Customer.objects.create(full_name=name, phone=phone)
        return customer

    def save(self, commit=True):
        parcel = super().save(commit=False)
        parcel.sender = self._customer_for("sender_phone", "sender_name")
        parcel.recipient = self._customer_for("recipient_phone", "recipient_name")
        if commit:
            parcel.save()
        return parcel


class TrackingUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=Parcel.Status.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    location = forms.CharField(
        max_length=180,
        required=False,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Mombasa branch",
            }
        ),
    )
    note = forms.CharField(
        max_length=240,
        required=False,
        strip=True,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Internal operational note (not shown publicly)",
            }
        ),
    )
