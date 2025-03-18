from django.shortcuts import render, get_object_or_404, redirect
from .models import Event, Race, RacePackage, Athlete, Registration
from .forms import AthleteRegistrationForm

def event_selection(request):
    """View to list all available events."""
    events = Event.objects.all()
    return render(request, 'registration/event_selection.html', {'events': events})


def race_selection(request, event_id):
    """View to list races under a selected event."""
    event = get_object_or_404(Event, id=event_id)
    races = event.races.all()  # Corrected query: fetch related races
    return render(request, 'registration/race_selection.html', {'event': event, 'races': races})


def package_selection(request, race_id):
    """View to list packages under a selected race."""
    race = get_object_or_404(Race, id=race_id)
    packages = race.packages.all()  # Corrected query: fetch related packages
    return render(request, 'registration/package_selection.html', {'race': race, 'packages': packages})


def athlete_registration(request, package_id):
    package = get_object_or_404(RacePackage, id=package_id)
    race = package.race  

    if request.method == 'POST':
        registration = Registration.objects.create()  # Create registration
        total_cost = 0  
        valid = True

        for i in range(len(request.POST.getlist('first_name'))):
            form_data = {
                'first_name': request.POST.getlist('first_name')[i],
                'last_name': request.POST.getlist('last_name')[i],
                'email': request.POST.getlist('email')[i],
                'phone': request.POST.getlist('phone')[i],
                'age': request.POST.getlist('age')[i],
                'sex': request.POST.getlist('sex')[i],
                'hometown': request.POST.getlist('hometown')[i]
            }

            form = AthleteRegistrationForm(form_data)
            if form.is_valid():
                athlete = form.save(commit=False)
                athlete.registration = registration  
                athlete.race = race
                athlete.package = package
                athlete.save()

                total_cost += package.price  # Calculate total cost
            else:
                valid = False
                registration.delete()  

        if valid:
            registration.total_amount = total_cost
            registration.save()
            return redirect('payment', registration_id=registration.id)

    return render(request, 'registration/athlete_registration.html', {
        'package': package,
        'forms': [AthleteRegistrationForm()]
    })
    
def payment_view(request, registration_id):
    registration = get_object_or_404(Registration, id=registration_id)

    if request.method == "POST":
        # Simulate successful payment (replace with actual payment gateway logic)
        registration.payment_status = "paid"
        registration.status = "completed"
        registration.save()

        return redirect('payment_success')  # Redirect to payment success page
    
    return render(request, "registration/payment.html", {"registration": registration})


def payment_success(request):
    return render(request, "registration/payment_success.html")


def payment_failed(request):
    return render(request, "registration/payment_failed.html")