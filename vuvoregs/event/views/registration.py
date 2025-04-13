"""Handles the athlete registration process and agreement to terms."""

from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from event.forms import BillingForm, athlete_formset_factory
from event.models import Race, RacePackage, Registration


def registration(request, race_id):
    """Display and process the multi-athlete registration form for a race.

    GET: Show empty formset
    POST: Validate athletes, create registration, and redirect to confirmation

    Template:
        registration/registration.html

    Context:
        race (Race): The selected race
        formset (FormSet): AthleteFormSet with one or more entries
        final_prices (dict): {package_id: calculated price}
        time_based_adjustment (TimeBasedPrice|None)
        min_participants (int)
    """
    race = get_object_or_404(Race, pk=race_id)
    event = race.event
    current_time = timezone.now()

    # ❌ Block if event is closed
    if not event.is_registration_open():
        return render(request, "registration/closed.html", {"event": event})

    # ⏳ Get any active time-based adjustment
    adjustment = race.time_based_prices.filter(
        start_date__lte=current_time, end_date__gte=current_time
    ).first()

    # 🎁 Filter packages for this race
    packages = RacePackage.objects.filter(
        event=event,
        races=race,
    ).filter(Q(visible_until__isnull=True) | Q(visible_until__gt=current_time))

    # 💰 Precalculate final prices per package for the UI
    time_adj = adjustment.price_adjustment if adjustment else Decimal("0.00")
    final_prices = {
        package.id: race.base_price_individual + package.price_adjustment + time_adj
        for package in packages
    }

    AthleteFormSet = athlete_formset_factory(race)

    if request.method == "POST":
        formset = AthleteFormSet(
            data=request.POST,
            form_kwargs={"race": race, "packages": packages},
            prefix="athlete",
            race=race,
        )
        formset.request = request  # used in form logic/JS

        if formset.is_valid():
            with transaction.atomic():
                # 📝 Create registration and athletes
                registration_instance = Registration.objects.create(event=event)
                athlete_instances = formset.save(commit=False)

                for athlete in athlete_instances:
                    athlete.registration = registration_instance
                    athlete.race = race
                    athlete.save()

                registration_instance.update_total_amount()

                return redirect(
                    "confirm_registration", registration_id=registration_instance.id
                )
        else:
            # ⚠️ Warn if not enough valid forms
            valid_forms = sum(
                1 for form in formset if form.is_valid() and form.has_changed()
            )
            if race.min_participants and valid_forms < race.min_participants:
                messages.warning(
                    request,
                    f"This race requires at least {race.min_participants} participants."
                    f"Please complete at least {race.min_participants} athlete forms.",
                )
    else:
        # 👋 Initial GET view
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


@require_http_methods(["GET", "POST"])
def confirm_registration(request, registration_id):
    """Show the T&Cs agreement step before payment is created.

    GET: Display terms, billing email, and confirm button
    POST: Record agreement and redirect to payment creation

    Template:
        registration/confirm.html

    Context:
        registration (Registration)
        athletes (QuerySet[Athlete])
        billing_form (BillingForm)
        event (Event)
    """
    registration = get_object_or_404(Registration, pk=registration_id)
    athletes = registration.athletes.select_related("package", "race")
    event = registration.event
    terms = getattr(event, "terms", None)

    if request.method == "POST":
        if request.POST.get("agrees_to_terms") != "on":
            messages.error(
                request,
                "You must agree to the Terms & Conditions before proceeding.",
            )
            return redirect("confirm_registration", registration_id=registration.id)

        registration.agrees_to_terms = True
        registration.agreed_to_terms = terms
        registration.save(update_fields=["agrees_to_terms", "agreed_to_terms"])

        return redirect("create_payment", registration_id=registration.id)

    form = BillingForm(
        initial={"billing_email": athletes[0].email if athletes else ""},
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
