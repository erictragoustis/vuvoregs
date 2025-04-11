"""View layer responsible for managing the full registration flow, including.

- Displaying upcoming events and associated races
- Handling multi-athlete race registration forms
- Dynamically providing package and pricing options via AJAX
- Integrating payment workflows (creation, confirmation, failure handling)
- Responding to webhooks and verifying payment statuses

This module orchestrates core interactions between athletes,
events, and the payment system.
"""

# Built-in libraries

from cities_light.models import City, Region

# Django core imports
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET

# Third-party packages
# Local app imports
from event.models import (
    RacePackage,
    RaceSpecialPrice,
    Registration,
)


# 📦 Return package options (AJAX endpoint)
def package_options(request, package_id):
    """Return JSON response containing available options for a given package.

    Used by dynamic UI elements (AJAX).
    """
    try:
        package = RacePackage.objects.get(pk=package_id)
    except RacePackage.DoesNotExist:
        return JsonResponse({"package_options": []})

    return JsonResponse({
        "package_options": [
            {"id": opt.id, "name": opt.name, "options_json": opt.options_json}
            for opt in package.packageoption_set.all()
        ]
    })


@require_GET
def special_price_options(request, race_id):
    """Return all special price options available for a given race."""
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


def load_regions(request):
    country_id = request.GET.get("country_id")
    regions = Region.objects.filter(country_id=country_id).order_by("name")
    return JsonResponse({"regions": list(regions.values("id", "name"))})


def load_cities(request):
    region_id = request.GET.get("region_id")
    cities = City.objects.filter(region_id=region_id).order_by("name")
    return JsonResponse({"cities": list(cities.values("id", "name"))})


# 🔁 Manual payment status checker — updates registration status from payment
def check_payment_status(request, registration_id):
    """Manually fetch and update the status of a payment related to a registration.

    Used for fallback or testing when auto webhooks aren't triggered.
    """
    registration = get_object_or_404(Registration, id=registration_id)

    if not registration.payment:
        messages.error(request, "No payment found for this registration.")
        return redirect("payment_failure", registration_id=registration.id)

    payment = registration.payment
    payment.fetch()
