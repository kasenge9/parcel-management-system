from django import forms
from .models import Branch, Customer, Parcel

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
            "delivery_fee": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["origin"].queryset = Branch.objects.filter(is_active=True)
        self.fields["destination"].queryset = Branch.objects.filter(is_active=True)

    def clean_weight_kg(self):
        value = self.cleaned_data["weight_kg"]
        if value <= 0:
            raise forms.ValidationError("Weight must be greater than zero.")
        return value

    def save(self, commit=True):
        parcel = super().save(commit=False)
        sender, _ = Customer.objects.get_or_create(phone=self.cleaned_data["sender_phone"].strip(), defaults={"full_name": self.cleaned_data["sender_name"].strip()})
        recipient, _ = Customer.objects.get_or_create(phone=self.cleaned_data["recipient_phone"].strip(), defaults={"full_name": self.cleaned_data["recipient_name"].strip()})
        parcel.sender, parcel.recipient = sender, recipient
        if commit:
            parcel.save()
        return parcel


class TrackingUpdateForm(forms.Form):
    status = forms.ChoiceField(choices=Parcel.Status.choices)
    location = forms.CharField(max_length=180, required=False)
    note = forms.CharField(max_length=240, required=False, widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Optional update for the customer"}))

    def clean_location(self):
        return self.cleaned_data["location"].strip()

    def clean_note(self):
        return self.cleaned_data["note"].strip()
