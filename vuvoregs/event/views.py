from django.shortcuts import render, get_object_or_404, redirect
from .models import Event, Race, RacePackage, Registration, PackageOption
from .forms import AthleteFormSet
from django.http import JsonResponse  # Import JsonResponse


def event_list(request):
    """Displays a list of available events."""
    events = Event.objects.filter(is_available=True)
    return render(request, 'registration/event_list.html', {'events': events})

def race_list(request, event_id):
    """Displays a list of races for a selected event."""
    event = get_object_or_404(Event, pk=event_id)
    races = Race.objects.filter(event=event)
    return render(request, 'registration/race_list.html', {'event': event, 'races': races})

def registration(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    event = race.event
    packages = RacePackage.objects.filter(event=event)

    if request.method == 'POST':
        formset = AthleteFormSet(request.POST, form_kwargs={'race': race, 'packages': packages})
        if formset.is_valid():
            registration_instance = Registration.objects.create() # create new registration.
            instances = formset.save(commit=False)
            total_amount = 0
            for instance in instances:
                instance.registration = registration_instance
                instance.race = race
                instance.save()
                total_amount += instance.package.price

            registration_instance.total_amount = total_amount
            registration_instance.save()

            return redirect('payment', registration_id=registration_instance.id)
        else:
            print(formset.errors)
    else:
        formset = AthleteFormSet(form_kwargs={'race': race, 'packages': packages})

    return render(request, 'registration/registration.html', {'race': race, 'formset': formset})


def package_options(request, package_id):
    package = get_object_or_404(RacePackage, pk=package_id)
    print(f"Package: {package}")  # Debug: Print the package
    options = PackageOption.objects.filter(package=package).values_list('options_json', flat=True)
    print(f"Options Queryset: {options}") # Debug: Print the queryset
    options_list = list(options)
    print(f"Options List: {options_list}") # Debug: print the list
    return JsonResponse({'options': options_list})

def payment(request, registration_id):
    """Handles payment processing for a registration."""
    registration = get_object_or_404(Registration, pk=registration_id)

    if request.method == 'POST':
        # Simulate payment processing (replace with actual payment gateway integration)
        payment_successful = True # Replace with actual payment logic

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

    return render(request, 'registration/payment.html', {'registration': registration}) # changed path

def payment_success(request, registration_id):
    """Displays a success message after successful payment."""
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(request, 'registration/payment_success.html', {'registration': registration}) # changed path

def payment_failure(request, registration_id):
    """Displays a failure message after unsuccessful payment."""
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(request, 'registration/payment_failure.html', {'registration': registration}) # changed path