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

from cities_light.models import City, Country, Region

# Django core imports
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from requests.exceptions import HTTPError

# Local app imports
from event.models import (
    Payment,
    Registration,
)

# Third-party packages
from payments import RedirectNeeded


# ✅ Payment completed — display confirmation page
def payment_success(request, registration_id):
    """Show the success page after a completed payment."""
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(
        request, "registration/payment_success.html", {"registration": registration}
    )


# ❌ Payment failed — display error/failure page
def payment_failure(request, registration_id):
    """Show the failure page when a payment is not successful."""
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(
        request, "registration/payment_failure.html", {"registration": registration}
    )


@require_POST
def create_payment(request, registration_id):
    """Creates a new payment instance and attaches it to the registration.

    Redirects to the provider's checkout or payment URL.
    """
    print("🔁 create_payment hit")
    print("📦 POST data:", request.POST.dict())

    registration = get_object_or_404(Registration, pk=registration_id)

    # ✅ Terms agreement check and save
    if request.POST.get("agrees_to_terms") != "on":
        messages.error(
            request, "You must agree to the Terms & Conditions before proceeding."
        )
        return redirect("confirm_registration", registration_id=registration.id)

    registration.agrees_to_terms = True
    registration.agreed_to_terms = registration.event.terms
    registration.save(update_fields=["agrees_to_terms", "agreed_to_terms"])

    # ✅ Prevent duplicate payment creation
    if registration.payment:
        try:
            form = registration.payment.get_form()
        except RedirectNeeded as redirect_to:
            return redirect(str(redirect_to))
        return HttpResponse("Unexpected error with existing payment.", status=500)

    # ✅ Country/Region/City
    country_id = request.POST.get("billing_country")
    region_id = request.POST.get("billing_region")
    city_id = request.POST.get("billing_city")

    country = Country.objects.filter(id=country_id).first()
    region = Region.objects.filter(id=region_id).first()
    city = City.objects.filter(id=city_id).first()

    # ✅ Create payment
    payment = Payment.objects.create(
        variant="viva",
        description=f"Registration #{registration.id}",
        total=registration.total_amount,
        currency="EUR",
        billing_first_name=request.POST.get("billing_first_name"),
        billing_last_name=request.POST.get("billing_last_name"),
        billing_address_1=request.POST.get("billing_address_1"),
        billing_address_2=request.POST.get("billing_address_2"),
        billing_postcode=request.POST.get("billing_postcode"),
        billing_country_code=country.code2 if country else None,
        billing_country_area=region.name if region else None,
        billing_city=city.name if city else None,
        billing_email=request.POST.get("billing_email"),
        billing_phone=str(request.POST.get("billing_phone")),  # ensure it's JSON-safe
        status="confirmed",
        captured_amount=0,
    )

    payment.registration = registration
    payment.save()

    registration.payment = payment
    registration.save()

    try:
        form = payment.get_form()
    except RedirectNeeded as redirect_to:
        return redirect(str(redirect_to))
    except HTTPError as e:
        print("❌ Viva Wallet API error:", e)
        messages.error(
            request,
            "There was a problem connecting to Viva Wallet. Please try again or contact support.",
        )
        return redirect("confirm_registration", registration_id=registration.id)
    except Exception as e:
        print("❌ Unexpected error:", e)
        messages.error(request, "An unexpected error occurred. Please try again.")
        return redirect("confirm_registration", registration_id=registration.id)
