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
import hashlib
import hmac
import json

from cities_light.models import City, Country, Region
from django.conf import settings

# Django core imports
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

# Third-party packages
from payments import PaymentStatus, RedirectNeeded

# Local app imports
from .forms import BillingForm, athlete_formset_factory
from .models import (
    Event,
    Payment,
    Race,
    RacePackage,
    RaceSpecialPrice,
    Registration,
    TermsAndConditions,
)


# 📅 List all upcoming events
def event_list(request):
    """Display a list of upcoming events sorted by date."""
    events = Event.objects.order_by("date")
    return render(request, "registration/event_list.html", {"events": events})


# 🏁 Show races under a selected event
def race_list(request, event_id):
    """Display the races associated with a specific event.

    If the event doesn't exist, show an appropriate message.
    """
    try:
        event = Event.objects.get(pk=event_id)
        races = Race.objects.filter(event=event)
    except Event.DoesNotExist:
        return render(
            request,
            "registration/race_list.html",
            {
                "event": None,
                "races": [],
                "message": "Registrations are closed for this event.",
            },
        )
    return render(
        request,
        "registration/race_list.html",
        {
            "event": event,
            "races": races,
        },
    )


# 📝 Handle multi-athlete registration for a race
def registration(request, race_id):
    """Display and process the multi-athlete registration form for a given race.

    Enforces event registration window and race minimum participants.
    """
    race = get_object_or_404(Race, pk=race_id)
    event = race.event

    # 🔒 Block registration if event is closed
    if not event.is_registration_open():
        return render(request, "registration/closed.html", {"event": event})

    packages = RacePackage.objects.filter(event=event, races=race)
    AthleteFormSet = athlete_formset_factory(race)

    if request.method == "POST":
        formset = AthleteFormSet(
            data=request.POST,
            form_kwargs={"race": race, "packages": packages},
            prefix="athlete",
            race=race,
        )
        formset.request = request  # inject request for validation/JS logic

        if formset.is_valid():
            with transaction.atomic():
                # 🎯 Create the registration
                registration_instance = Registration.objects.create(event=event)
                total_amount = 0

                # 💾 Save each athlete
                athlete_instances = formset.save(commit=False)
                for athlete_obj in athlete_instances:
                    athlete_obj.registration = registration_instance
                    athlete_obj.race = race  # required before calling get_final_price
                    athlete_obj.save()
                    total_amount += athlete_obj.get_final_price()

                registration_instance.total_amount = total_amount
                registration_instance.save()

                # ✅ No payment creation here — defer to confirmation view
                return redirect(
                    "confirm_registration", registration_id=registration_instance.id
                )

        else:
            # 🧼 JS handles UI validation — avoid repeating warnings
            valid_forms = sum(
                1 for form in formset if form.is_valid() and form.has_changed()
            )
            if race.min_participants and valid_forms < race.min_participants:
                messages.warning(
                    request,
                    f"This race requires at least {race.min_participants} participants. "  # noqa: E501
                    f"Please complete at least {race.min_participants} athlete forms.",
                )
    else:
        formset = AthleteFormSet(
            form_kwargs={"race": race, "packages": packages},
            prefix="athlete",
            race=race,
        )
        formset.request = request

    return render(
        request,
        "registration/registration.html",
        {
            "race": race,
            "formset": formset,
            "min_participants": race.min_participants or 1,
        },
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


# 📜 Display and handle Terms & Conditions agreement
@require_http_methods(["GET", "POST"])
def confirm_registration(request, registration_id):
    """Show confirmation screen and handle agreement to T&Cs."""
    registration = get_object_or_404(Registration, pk=registration_id)
    athletes = registration.athletes.select_related("package", "race")
    event = registration.event
    terms = getattr(event, "terms", None)

    if request.method == "POST":
        if request.POST.get("agrees_to_terms") != "on":
            messages.error(
                request, "You must agree to the Terms & Conditions before proceeding."
            )
            return redirect("confirm_registration", registration_id=registration.id)

        # ✅ Save T&C agreement
        registration.agrees_to_terms = True
        registration.agreed_to_terms = terms
        registration.save()

    # Initial form rendering
    from .forms import BillingForm

    form = BillingForm(
        initial={
            "billing_email": athletes[0].email if athletes else "",
        }
    )
    return render(
        request,
        "registration/confirm.html",
        {
            "registration": registration,
            "athletes": athletes,
            "event": event,
            "billing_form": form,
        },
    )


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

    if payment.status == "confirmed":
        registration.payment_status = "paid"
        registration.status = "completed"
        messages.success(request, "✅ Payment confirmed.")
    elif payment.status in ["rejected", "error", "expired"]:
        registration.payment_status = "failed"
        registration.status = "failed"
        messages.error(request, "❌ Payment failed or expired.")
    else:
        messages.info(request, f"ℹ️ Payment is still in progress: {payment.status}")

    registration.save()

    return redirect(
        "payment_success"
        if registration.payment_status == "paid"
        else "payment_failure",
        registration_id=registration.id,
    )


@csrf_exempt
def payment_webhook(request):
    """Webhook endpoint to receive automatic payment updates.

    Supports the dummy provider (no `.fetch()` call).
    """
    try:
        data = json.loads(request.body)
        payment_id = data.get("payment_id")
        if not payment_id:
            return JsonResponse(
                {"status": "error", "message": "Missing payment_id"}, status=400
            )

        payment = Payment.objects.get(id=payment_id)

        # ✅ Don't call fetch — dummy provider doesn't support it
        if hasattr(payment, "registration"):
            registration = payment.registration

            if payment.status == "confirmed":
                registration.payment_status = "paid"
                registration.status = "completed"
            elif payment.status in ["rejected", "error", "expired"]:
                registration.payment_status = "failed"
                registration.status = "failed"

            registration.save()

        return JsonResponse({"status": "success"})

    except Payment.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Invalid payment_id"}, status=404
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


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


@require_POST
def create_payment(request, registration_id):
    """Creates a new payment instance and attaches it to the registration.

    Redirects to the provider's checkout or payment URL.
    """
    print("🔁 create_payment hit")
    print("📦 POST data:", request.POST.dict())
    registration = get_object_or_404(Registration, pk=registration_id)

    if registration.payment:
        try:
            form = registration.payment.get_form()
        except RedirectNeeded as redirect_to:
            return redirect(str(redirect_to))
        return HttpResponse(
            "Unexpected error with existing payment.", status=500
        )  # or raise

    country_id = request.POST.get("billing_country")
    region_id = request.POST.get("billing_region")
    city_id = request.POST.get("billing_city")

    country = Country.objects.filter(id=country_id).first()
    region = Region.objects.filter(id=region_id).first()
    city = City.objects.filter(id=city_id).first()

    # First save Payment to generate a PK before using get_form (which calls .save(update_fields=...))
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
        billing_phone=str(request.POST.get("billing_phone")),  # ensure JSON safe
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


def load_regions(request):
    country_id = request.GET.get("country_id")
    regions = Region.objects.filter(country_id=country_id).order_by("name")
    return JsonResponse({"regions": list(regions.values("id", "name"))})


def load_cities(request):
    region_id = request.GET.get("region_id")
    cities = City.objects.filter(region_id=region_id).order_by("name")
    return JsonResponse({"cities": list(cities.values("id", "name"))})


def viva_payment_success(request, transaction_id):
    payment = get_object_or_404(Payment, transaction_id=transaction_id)
    registration = getattr(payment, "registration", None)

    if payment.status != PaymentStatus.CONFIRMED:
        payment.status = PaymentStatus.CONFIRMED
        payment.save()

        if registration:
            registration.payment_status = "paid"
            registration.status = "completed"
            registration.save()

    return redirect("payment_success", registration_id=registration.id)


def viva_payment_failure(request, transaction_id):
    payment = get_object_or_404(Payment, transaction_id=transaction_id)
    registration = getattr(payment, "registration", None)
    if not registration:
        return HttpResponse(
            "Payment found but not linked to any registration.", status=500
        )

    if payment.status != PaymentStatus.ERROR:
        payment.status = PaymentStatus.ERROR
        payment.save()

        if registration:
            registration.payment_status = "failed"
            registration.status = "failed"
            registration.save()

    return redirect("payment_failure", registration_id=registration.id)


def viva_success_redirect_handler(request):
    order_code = request.GET.get("s")  # 't' is Viva's transaction ref
    if not order_code:
        return HttpResponse("Missing order code", status=400)
    return redirect("viva_payment_success", transaction_id=order_code)


@csrf_exempt
def payment_webhook(request):
    """Handles webhook notifications from Viva Wallet for transaction events.

    - Expects POST with Viva event JSON payload.
    - EventData.transactionId is used to locate the related payment.
    - Uses EventTypeId to decide status update.
    """
    if request.method == "GET":
        return JsonResponse({"Key": settings.VIVA_WEBHOOK_VERIFICATION_KEY})

    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        payload = json.loads(request.body)
        event_type_id = payload.get("EventTypeId")
        transaction_data = payload.get("EventData", {})
        transaction_id = transaction_data.get("TransactionId")

        print("📬 Webhook received:", event_type_id, transaction_id)

        if not transaction_id:
            return JsonResponse(
                {"status": "error", "message": "Missing TransactionId"}, status=400
            )

        # Find payment with that transaction ID stored in extra_data (assumed format)
        payment = Payment.objects.filter(extra_data__icontains=transaction_id).first()
        if not payment:
            return JsonResponse(
                {"status": "error", "message": "Payment not found"}, status=404
            )

        if event_type_id == 1796:  # Transaction Payment Created
            payment.status = "confirmed"
        elif event_type_id == 1798:  # Transaction Failed
            payment.status = "rejected"
        elif event_type_id == 1797:  # Transaction Reversal (refund)
            payment.status = "refunded"
        else:
            return JsonResponse({
                "status": "ignored",
                "message": "Unhandled EventTypeId",
            })

        payment.save()

        if hasattr(payment, "registration"):
            registration = payment.registration
            if payment.status == "confirmed":
                registration.status = "completed"
                registration.payment_status = "paid"
            elif payment.status == "rejected":
                registration.status = "failed"
                registration.payment_status = "failed"
            elif payment.status == "refunded":
                registration.status = "refunded"
                registration.payment_status = "refunded"
            registration.save()

        return JsonResponse({"status": "success"})

    except Exception as e:
        print("❗ Webhook error:", str(e))
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
