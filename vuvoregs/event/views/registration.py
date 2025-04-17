"""Handles the athlete registration process and agreement to terms."""

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from event.forms import BillingForm, athlete_formset_factory
from event.models import Race, Registration
from django.utils.translation import gettext_lazy as _


@require_http_methods(["GET", "POST"])
def registration(request, race_id):
    """Display and process the multi-athlete registration form for a race."""
    race = get_object_or_404(Race, pk=race_id)
    event = race.event

    if not event.is_registration_open():
        return render(request, "registration/closed.html", {"event": event})

    AthleteFormSet = athlete_formset_factory(race)

    formset_kwargs = {
        "form_kwargs": {"race": race},
        "prefix": "athlete",
        "race": race,
    }

    if request.method == "POST":
        formset = AthleteFormSet(data=request.POST, **formset_kwargs)
        formset.setRequest(request)

        if formset.is_valid():
            try:
                with transaction.atomic():
                    registration = Registration.objects.create(event=event)
                    athletes = formset.save(commit=False)

                    for athlete in athletes:
                        athlete.registration = registration
                        athlete.race = race
                        athlete.save()

                    registration.update_total_amount()

                    return redirect(
                        "confirm_registration", registration_id=registration.id
                    )

            except Exception as e:
                messages.error(
                    request,
                    f"Oops! Something went wrong during registration: {e}",
                )
                return redirect(request.path)

        else:
            messages.warning(
                request,
                _("Please fix the errors below and try again."),
            )

    else:
        formset = AthleteFormSet(**formset_kwargs)
        formset.setRequest(request)

    return render(
        request,
        "registration/registration.html",
        {
            "race": race,
            "formset": formset,
            "min_participants": race.min_participants or 1,
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
    any_minor = any(a.is_minor() for a in athletes)
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
            "requires_parental_consent": any_minor and event.parental_declaration,
        },
    )
