# Django core imports
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.timezone import now
from django.views.decorators.http import require_http_methods

# Local app imports
from event.forms import BillingForm, athlete_formset_factory
from event.models import (
    Race,
    RacePackage,
    Registration,
)


# 📝 Handle multi-athlete registration for a race
def registration(request, race_id):
    """Display and process the multi-athlete registration form for a given race.

    Enforces event registration window and race minimum participants.
    """
    race = get_object_or_404(Race, pk=race_id)
    event = race.event
    current_time = timezone.now()
    adjustment = None

    for tbp in race.time_based_prices.all():
        if tbp.start_date <= current_time <= tbp.end_date:
            adjustment = tbp
            break

    # 🔒 Block registration if event is closed
    if not event.is_registration_open():
        return render(request, "registration/closed.html", {"event": event})

    packages = RacePackage.objects.filter(event=event, races=race).filter(
        Q(visible_until__isnull=True) | Q(visible_until__gt=current_time)
    )

    final_prices = {}
    base_price = race.base_price_individual
    time_adj = adjustment.price_adjustment if adjustment else Decimal("0.00")

    for package in packages:
        final = base_price + package.price_adjustment + time_adj
        final_prices[package.id] = final

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
            "time_based_adjustment": adjustment,
            "final_prices": final_prices,
        },
    )


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
        registration.save(update_fields=["agrees_to_terms", "agreed_to_terms"])

        return redirect("create_payment", registration_id=registration.id)

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
