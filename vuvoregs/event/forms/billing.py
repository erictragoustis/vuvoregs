"""This module defines the BillingForm for handling billing-related data in forms.

The form includes fields for billing details such as name, address,
country, region, city, phone, and email.
"""

from cities_light.models import City, Country, Region
from django import forms


class BillingForm(forms.Form):  # noqa: D101
    billing_first_name = forms.CharField(max_length=100)
    billing_last_name = forms.CharField(max_length=100)
    billing_address_1 = forms.CharField(max_length=255)
    billing_address_2 = forms.CharField(max_length=255, required=False)
    billing_postcode = forms.CharField(max_length=20)
    billing_country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        widget=forms.Select(attrs={"class": "form-select", "id": "billing-country"}),
    )
    billing_region = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "id": "billing-region"}),
        required=False,
    )
    billing_city = forms.ModelChoiceField(
        queryset=City.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "id": "billing-city"}),
    )
    billing_phone = forms.CharField(max_length=20)
    billing_email = forms.EmailField()
