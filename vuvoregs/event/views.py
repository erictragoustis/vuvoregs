from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils.timezone import now
from django.db import transaction
from django.db.models import Q, Count, F
from django.contrib import messages

from .models import Event, Race, RacePackage, Registration
from .forms import athlete_formset_factory

# 📅 List all upcoming events
def event_list(request):
    events = Event.objects.order_by('date')
    return render(request, 'registration/event_list.html', {'events': events})

# 🏁 Show races under a selected event
def race_list(request, event_id):
    try:
        event = Event.objects.get(pk=event_id)
        races = Race.objects.filter(event=event)
    except Event.DoesNotExist:
        return render(request, 'registration/race_list.html', {
            'event': None,
            'races': [],
            'message': "Registrations are closed for this event."
        })
    return render(request, 'registration/race_list.html', {
        'event': event,
        'races': races,
    })

# 📝 Handle multi-athlete registration for a race
def registration(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    event = race.event

    if not event.is_registration_open():
        return render(request, 'registration/closed.html', {'event': event})

    packages = RacePackage.objects.filter(event=event)
    AthleteFormSet = athlete_formset_factory(race)

    if request.method == 'POST':
        formset = AthleteFormSet(
            data=request.POST,
            form_kwargs={'race': race, 'packages': packages},
            prefix='athlete',
            race=race
        )
        # 🔌 Inject request context manually into formset
        formset.request = request

        if formset.is_valid():
            with transaction.atomic():
                registration_instance = Registration.objects.create(event=event)
                total_amount = 0

                athlete_instances = formset.save(commit=False)
                for athlete_obj in athlete_instances:
                    athlete_obj.registration = registration_instance
                    athlete_obj.race = race
                    athlete_obj.save()
                    total_amount += athlete_obj.package.price

                registration_instance.total_amount = total_amount
                registration_instance.save()

            return redirect('payment', registration_id=registration_instance.id)
        else:
  
            valid_forms = sum(1 for form in formset if form.is_valid() and form.has_changed())
            if race.min_participants and valid_forms < race.min_participants:
                # 📣 Rely on universal toast — no duplicate warning needed if JS handles it
                messages.warning(
                    request,
                    f"This race requires at least {race.min_participants} participants. "
                    f"Please complete at least {race.min_participants} athlete forms."
                )
    else:
        formset = AthleteFormSet(
            form_kwargs={'race': race, 'packages': packages},
            prefix='athlete',
            race=race
        )
        # 🔌 Inject request for GET too (needed if any JS pulls form data)
        formset.request = request

    return render(request, 'registration/registration.html', {
        'race': race,
        'formset': formset,
        'min_participants': race.min_participants or 1
    })

# 📦 Return package options as JSON (used by JS)
def package_options(request, package_id):
    try:
        package = RacePackage.objects.get(pk=package_id)
    except RacePackage.DoesNotExist:
        return JsonResponse({'package_options': []})

    return JsonResponse({
        'package_options': [
            {'id': opt.id, 'name': opt.name, 'options_json': opt.options_json}
            for opt in package.packageoption_set.all()
        ]
    })

# 💳 Fake payment flow
def payment(request, registration_id):
    registration = get_object_or_404(Registration, pk=registration_id)
    if request.method == 'POST':
        success = request.POST.get("mock_fail") != "1"
        registration.payment_status = 'paid' if success else 'failed'
        registration.status = 'completed' if success else 'failed'
        registration.save()
        return redirect(
            'payment_success' if success else 'payment_failure',
            registration_id=registration.id
        )

    return render(request, 'registration/payment.html', {
        'registration': registration
    })

# ✅ Payment result pages
def payment_success(request, registration_id):
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(request, 'registration/payment_success.html', {
        'registration': registration
    })

def payment_failure(request, registration_id):
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(request, 'registration/payment_failure.html', {
        'registration': registration
    })
