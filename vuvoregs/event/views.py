from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils.timezone import now
from django.db import transaction
from django.db.models import Q, Count, F
import json

from .models import Event, Race, RacePackage, Registration, Athlete
from .forms import athlete_formset_factory


# ================================
# 📅  List All Available Events
# ================================
def event_list(request):
    """
    Displays a list of all upcoming events, ordered by date.
    """
    events = Event.objects.order_by('date')
    return render(request, 'registration/event_list.html', {'events': events})


# ================================
# 🏁  List Races in an Event
# ================================
def race_list(request, event_id):
    """
    Displays races associated with a specific event.
    If the event doesn't exist, return a graceful message.
    """
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


# ================================
# 📝  Athlete Registration Flow
# ================================
def registration(request, race_id):
    """
    Handles the athlete registration for a race.
    - Shows one or more forms based on race.min_participants
    - Filters available packages and pickup points based on event
    - Collects package options via JS and stores them as JSON
    """
    race = get_object_or_404(Race, pk=race_id)
    event = race.event

    if not event.is_registration_open():
        return render(request, 'registration/closed.html', {'event': event})

    packages = RacePackage.objects.filter(event=event)
    AthleteFormSet = athlete_formset_factory(race)

    if request.method == 'POST':
        # Inject race/packages context into each form
        formset = AthleteFormSet(
            request.POST,
            form_kwargs={'race': race, 'packages': packages}
        )

        if formset.is_valid():
            with transaction.atomic():
                registration_instance = Registration.objects.create(event=event)
                total_amount = 0

                instances = formset.save(commit=False)

                for index, instance in enumerate(instances):
                    instance.registration = registration_instance
                    instance.race = race

                    # Handle dynamic package options submitted via JS
                    selected_options = {}
                    for key in request.POST:
                        if key.startswith(f'athlete-{index}-option-') and not key.endswith('-name'):
                            option_id = key.split(f'athlete-{index}-option-')[-1]
                            option_name_key = f'{key}-name'
                            option_name = request.POST.get(option_name_key, f'Option {option_id}')
                            values = request.POST.getlist(key)

                            if values:
                                selected_options[option_name] = values

                    try:
                        instance.selected_options = json.loads(json.dumps(selected_options))
                    except (ValueError, TypeError):
                        instance.selected_options = None

                    instance.save()
                    total_amount += instance.package.price

                registration_instance.total_amount = total_amount
                registration_instance.save()

            return redirect('payment', registration_id=registration_instance.id)

        else:
            print("Formset errors:", formset.errors)

    else:
        formset = AthleteFormSet(form_kwargs={'race': race, 'packages': packages})

    return render(request, 'registration/registration.html', {
        'race': race,
        'formset': formset
    })


# ================================
# 🔄  AJAX: Package Option Loader
# ================================
def package_options(request, package_id):
    """
    Returns JSON data for all options attached to a given package.
    Used by frontend JS to dynamically render package options.
    """
    try:
        package = RacePackage.objects.get(pk=package_id)
        package_options_data = [
            {
                'id': option.id,
                'name': option.name,
                'options_json': option.options_json
            }
            for option in package.packageoption_set.all()
        ]
        return JsonResponse({'package_options': package_options_data})
    except RacePackage.DoesNotExist:
        return JsonResponse({'package_options': []})


# ================================
# 💳  Payment (Mocked)
# ================================
def payment(request, registration_id):
    """
    Simulates payment processing for a registration.
    (Replace with real gateway integration like Stripe or Razorpay.)
    """
    registration = get_object_or_404(Registration, pk=registration_id)

    if request.method == 'POST':
        # Placeholder for real payment success
        payment_successful = request.POST.get("mock_fail") != "1"

        if payment_successful:
            registration.payment_status = 'paid'
            registration.status = 'completed'
            registration.save()
            return redirect('payment_success', registration_id=registration.id)
        else:
            registration.payment_status = 'failed'
            registration.status = 'failed'
            registration.save()
            return redirect('payment_failure', registration_id=registration.id)

    return render(request, 'registration/payment.html', {'registration': registration})


# ================================
# ✅  Payment Success
# ================================
def payment_success(request, registration_id):
    """
    Thank-you page for successful payments.
    """
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(request, 'registration/payment_success.html', {'registration': registration})


# ================================
# ❌  Payment Failure
# ================================
def payment_failure(request, registration_id):
    """
    Error page for failed payments.
    """
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(request, 'registration/payment_failure.html', {'registration': registration})
