"""View layer responsible for managing the full registration flow.

Responsibilities:
- Displaying upcoming events and associated races
- Handling multi-athlete registration
- Managing payment creation, success, failure
- Tracking webhook and billing state
"""

from cities_light.models import City, Country, Region
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from requests.exceptions import HTTPError

from event.models import Payment, Registration
from payments import RedirectNeeded


def payment_success(request, registration_id):
    """Display a success page after a successful payment.

    Template:
        registration/payment_success.html

    Context:
        registration (Registration)
    """
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(
        request,
        "registration/payment_success.html",
        {"registration": registration},
    )


def payment_failure(request, registration_id):
    """Display a failure page if the payment failed or was cancelled.

    Template:
        registration/payment_failure.html

    Context:
        registration (Registration)
    """
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(
        request,
        "registration/payment_failure.html",
        {"registration": registration},
    )


@require_POST
def create_payment(request, registration_id):
    """Create a new payment instance and redirect to the Viva Wallet checkout.

    Steps:
    - Validate agreement to terms
    - Avoid duplicate payment creation
    - Collect billing address (with cities-light)
    - Create and store payment
    - Redirect to provider

    Redirects:
        - On success → Viva Wallet
        - On error → confirm_registration
    """
    registration = get_object_or_404(Registration, pk=registration_id)

    # 🔒 Ensure agreement to T&Cs (also checked in confirm view)
    if request.POST.get("agrees_to_terms") != "on":
        messages.error(
            request,
            "You must agree to the Terms & Conditions before proceeding.",
        )
        return redirect("confirm_registration", registration_id=registration.id)

    registration.agrees_to_terms = True
    registration.agreed_to_terms = registration.event.terms
    registration.save(update_fields=["agrees_to_terms", "agreed_to_terms"])

    # 🚫 Prevent creating a second payment
    if registration.payment:
        try:
            form = registration.payment.get_form()
        except RedirectNeeded as redirect_to:
            return redirect(str(redirect_to))
        return HttpResponse("Unexpected error: payment already exists.", status=500)

    # 🏙 Parse billing location via cities-light
    country = Country.objects.filter(id=request.POST.get("billing_country")).first()
    region = Region.objects.filter(id=request.POST.get("billing_region")).first()
    city = City.objects.filter(id=request.POST.get("billing_city")).first()

    # 💳 Create the actual payment object
    payment = Payment.objects.create(
        variant="viva",  # Payment provider
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
        billing_phone=str(request.POST.get("billing_phone")),
        status="confirmed",
        captured_amount=0,
    )

    # 🔗 Link payment to registration
    payment.registration = registration
    payment.save()
    registration.payment = payment
    registration.save(update_fields=["payment"])

    # 🚀 Get the checkout form and redirect to Viva Wallet
    try:
        form = payment.get_form()  # noqa: F841
    except RedirectNeeded as redirect_to:
        return redirect(str(redirect_to))

    # ⚠️ Handle known errors
    except HTTPError as e:
        if settings.DEBUG:
            print("❌ Viva Wallet API error:", e)
        messages.error(
            request,
            "There was a problem connecting to Viva Wallet. "
            "Please try again or contact support.",
        )
        return redirect("confirm_registration", registration_id=registration.id)

    except Exception as e:
        if settings.DEBUG:
            print("❌ Unexpected error:", e)
        messages.error(
            request,
            "An unexpected error occurred. Please try again.",
        )
        return redirect("confirm_registration", registration_id=registration.id)

    return HttpResponse("Unexpected outcome", status=500)
