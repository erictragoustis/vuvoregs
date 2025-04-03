from django.shortcuts import render, get_object_or_404, redirect
from .models import Event, Race, RacePackage, Registration, PackageOption, Athlete
from .forms import athlete_formset_factory
from django.http import JsonResponse

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
    AthleteFormSet = athlete_formset_factory(race)

    if request.method == 'POST':
        formset = AthleteFormSet(request.POST, form_kwargs={'race': race, 'packages': packages})
        if formset.is_valid():
            registration_instance = Registration.objects.create(event=event)
            instances = formset.save(commit=False)
            total_amount = 0
            
            for index, instance in enumerate(instances):
                instance.registration = registration_instance
                instance.race = race
                instance.save()
                total_amount += instance.package.price
                selected_options = {}
                
                for package_option in instance.package.packageoption_set.all():
                    key = f'athlete-{index}-option-{package_option.id}'
                    selected_values = request.POST.getlist(key)
                    print(f"Checking Key: {key} -> Values:", selected_values)  # Debug
                    
                    if selected_values:
                        # Store options as a list inside the dictionary
                        selected_options[package_option.name] = selected_values

                # Ensure selected_options is stored correctly as JSON
                print(f"Athlete {index} - Selected Options:", selected_options)
                instance.selected_options = selected_options if selected_options else None
                instance.save()
            print("POST Data:", request.POST)
            registration_instance.total_amount = total_amount
            registration_instance.save()
            return redirect('payment', registration_id=registration_instance.id)
        else:
            print(formset.errors)
        print("POST Data:", request.POST)
    else:
        formset = AthleteFormSet(form_kwargs={'race': race, 'packages': packages})

    return render(request, 'registration/registration.html', {'race': race, 'formset': formset})

def package_options(request, package_id):
    try:
        package = RacePackage.objects.get(pk=package_id)
        package_options_data = [{'id': option.id, 'name': option.name, 'options_json': option.options_json} for option in package.packageoption_set.all()]
        return JsonResponse({'package_options': package_options_data})
    except RacePackage.DoesNotExist:
        return JsonResponse({'package_options': []})

def payment(request, registration_id):
    """Handles payment processing for a registration."""
    registration = get_object_or_404(Registration, pk=registration_id)

    if request.method == 'POST':
        payment_successful = True 
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

def payment_success(request, registration_id):
    """Displays a success message after successful payment."""
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(request, 'registration/payment_success.html', {'registration': registration})

def payment_failure(request, registration_id):
    """Displays a failure message after unsuccessful payment."""
    registration = get_object_or_404(Registration, pk=registration_id)
    return render(request, 'registration/payment_failure.html', {'registration': registration})
