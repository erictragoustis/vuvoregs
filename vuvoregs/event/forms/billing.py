"""Form definition for collecting billing details during registration checkout.

Includes:
- First/last name
- Address and postal code
- Country → Region → City cascade using django-cities-light
- Phone and email
"""

from cities_light.models import City, Country, Region
from django import forms


class BillingForm(forms.Form):
    """
    Form for capturing billing address and contact info.

    Used during the payment step of the registration process.
    """

    billing_first_name = forms.CharField(
        max_length=100,
        label="First Name",
    )
    billing_last_name = forms.CharField(
        max_length=100,
        label="Last Name",
    )

    billing_address_1 = forms.CharField(
        max_length=255,
        label="Address Line 1",
    )
    billing_address_2 = forms.CharField(
        max_length=255,
        required=False,
        label="Address Line 2 (optional)",
    )

    billing_postcode = forms.CharField(
        max_length=20,
        label="Postal Code",
    )

    billing_country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        widget=forms.Select(attrs={"class": "form-select", "id": "billing-country"}),
        label="Country",
    )
    billing_region = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "billing-region"}),
        label="Region",
    )
    billing_city = forms.ModelChoiceField(
        queryset=City.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "id": "billing-city"}),
        label="City",
    )

    billing_phone = forms.CharField(
        max_length=20,
        label="Phone Number",
    )
    billing_email = forms.EmailField(
        label="Email Address",
    )
