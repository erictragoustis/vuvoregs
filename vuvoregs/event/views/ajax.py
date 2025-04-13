"""AJAX and fallback views for dynamic UI and payment status updates.

Includes:
- Dynamic package/special price loaders
- Country/region/city population for billing form
- Manual fallback payment status refresh
"""

from cities_light.models import City, Region
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET

from event.models import (
    RacePackage,
    RaceSpecialPrice,
    Registration,
)


@require_GET
def package_options(request, package_id):
    """Return all options related to a RacePackage as JSON.

    Used by JS when user selects a package in the form.

    Response format:
        {
            "package_options": [
                {"id": 1, "name": "T-shirt Size", "options_json": [...]},
                ...
            ]
        }
    """
    try:
        package = RacePackage.objects.get(pk=package_id)
    except RacePackage.DoesNotExist:
        return JsonResponse({"package_options": []})

    return JsonResponse({
        "package_options": [
            {
                "id": opt.id,
                "name": opt.name,
                "options_json": opt.options_json,
            }
            for opt in package.packageoption_set.all()
        ]
    })


@require_GET
def special_price_options(request, race_id):
    """Return all available special pricing options for a given race.

    Response format:
        {
            "special_prices": [
                {"id": 3, "label": "Student Discount", "discount_amount": "5.00"},
                ...
            ]
        }
    """
    special_prices = RaceSpecialPrice.objects.filter(race_id=race_id)

    return JsonResponse({
        "special_prices": [
            {
                "id": sp.id,
                "label": sp.label,
                "discount_amount": str(sp.discount_amount),
            }
            for sp in special_prices
        ]
    })


@require_GET
def load_regions(request):
    """Return regions for a given country ID (for dynamic billing selection).

    Response format:
        {"regions": [{"id": 1, "name": "Attica"}, ...]}
    """
    country_id = request.GET.get("country_id")
    regions = Region.objects.filter(country_id=country_id).order_by("name")
    return JsonResponse({"regions": list(regions.values("id", "name"))})


@require_GET
def load_cities(request):
    """Return cities for a given region ID (for dynamic billing selection).

    Response format:
        {"cities": [{"id": 2, "name": "Athens"}, ...]}
    """
    region_id = request.GET.get("region_id")
    cities = City.objects.filter(region_id=region_id).order_by("name")
    return JsonResponse({"cities": list(cities.values("id", "name"))})


@require_GET
def check_payment_status(request, registration_id):
    """Manually re-check the payment status of a registration.

    Used as a fallback when webhook notifications fail or are delayed.
    """
    registration = get_object_or_404(Registration, id=registration_id)

    if not registration.payment:
        messages.error(request, "No payment found for this registration.")
        return redirect("payment_failure", registration_id=registration.id)

    if settings.DEBUG:
        print("🔄 Manually fetching payment status for registration", registration.id)

    registration.payment.fetch()
    return redirect("payment_success", registration_id=registration.id)
