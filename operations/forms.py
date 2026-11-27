from django import forms

from .models import Branch, County, Customer, OperatorRoute, OperatorServicePoint, Parcel, Town


class ParcelForm(forms.ModelForm):
    sender_name = forms.CharField(max_length=160, label="Sender name")
    sender_phone = forms.CharField(max_length=30, label="Sender phone")
    recipient_name = forms.CharField(max_length=160, label="Recipient name")
    recipient_phone = forms.CharField(max_length=30, label="Recipient phone")
    destination_county = forms.ModelChoiceField(queryset=County.objects.all(), label="Destination county")
    destination_town = forms.ModelChoiceField(queryset=Town.objects.none(), label="Destination town")
    operator_route = forms.ModelChoiceField(
        queryset=OperatorRoute.objects.none(), required=False,
        label="Delivery operator / route",
        empty_label="Leave route unassigned — assign later",
    )
    operator_service_point = forms.ModelChoiceField(
        queryset=OperatorServicePoint.objects.none(), required=False,
        label="Receiving courier service point",
        empty_label="No receiving service point selected",
    )

    class Meta:
        model = Parcel
        fields = ["description", "weight_kg", "origin", "delivery_fee"]
        widgets = {
            "description": forms.TextInput(attrs={"placeholder": "Documents or parcel contents"}),
            "weight_kg": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "delivery_fee": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["origin"].queryset = Branch.objects.filter(is_active=True).select_related("town")
        county_id = self.data.get("destination_county") or self.initial.get("destination_county")
        towns = Town.objects.select_related("county").all()
        if county_id:
            towns = towns.filter(county_id=county_id)
        self.fields["destination_town"].queryset = towns
        self.fields["operator_route"].queryset = OperatorRoute.objects.filter(
            is_active=True,
            parcel_service_confirmed=True,
            operator__is_active=True,
            operator__parcel_service_confirmed=True,
            verification_status__in=[
                OperatorRoute.Verification.PUBLISHED,
                OperatorRoute.Verification.CONFIRMED,
            ],
        ).select_related("operator", "origin", "destination")
        self.fields["operator_service_point"].queryset = OperatorServicePoint.objects.filter(
            is_active=True,
            is_verified=True,
            accepts_parcels=True,
            operator__is_active=True,
            operator__parcel_service_confirmed=True,
        ).select_related("operator", "town")

    def clean(self):
        cleaned = super().clean()
        route = cleaned.get("operator_route")
        origin = cleaned.get("origin")
        destination_town = cleaned.get("destination_town")
        service_point = cleaned.get("operator_service_point")
        if route and destination_town and route.destination_id != destination_town.id:
            self.add_error("operator_route", "This operator route does not serve the selected destination town.")
        if route and origin and not origin.town_id:
            self.add_error("operator_route", "Set the origin branch town before selecting an operator route.")
        elif route and origin and route.origin_id != origin.town_id:
            self.add_error("operator_route", "This operator route does not start at the selected origin branch town.")
        if service_point and destination_town and service_point.town_id != destination_town.id:
            self.add_error("operator_service_point", "This service point is not in the selected destination town.")
        if route and service_point and route.operator_id != service_point.operator_id:
            self.add_error("operator_service_point", "The route and service point must belong to the same operator.")
        return cleaned

    def clean_weight_kg(self):
        value = self.cleaned_data["weight_kg"]
        if value <= 0:
            raise forms.ValidationError("Weight must be greater than zero.")
        return value

    def save(self, commit=True):
        parcel = super().save(commit=False)
        sender, _ = Customer.objects.get_or_create(
            phone=self.cleaned_data["sender_phone"].strip(),
            defaults={"full_name": self.cleaned_data["sender_name"].strip()},
        )
        recipient, _ = Customer.objects.get_or_create(
            phone=self.cleaned_data["recipient_phone"].strip(),
            defaults={"full_name": self.cleaned_data["recipient_name"].strip()},
        )
        parcel.sender, parcel.recipient = sender, recipient
        parcel.destination = None
        parcel.destination_town = self.cleaned_data["destination_town"]
        parcel.operator_route = self.cleaned_data.get("operator_route")
        parcel.operator_service_point = self.cleaned_data.get("operator_service_point")
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
