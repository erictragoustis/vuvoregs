from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from event.models import Event, Registration, Athlete
from django.db.models import Q
from django.core.paginator import Paginator

@staff_member_required
def dashboard_home(request):
    # Dummy stats for now
    context = {
        'total_registrations': 120,
        'paid_count': 85,
        'unpaid_count': 35,
    }
    return render(request, 'dashboard/home.html', context)

@staff_member_required
def registration_list(request):
    # Organizer filtering
    if request.user.is_staff:
        events = Event.objects.all()
    else:
        events = Event.objects.filter(organizer=request.user)

    # GET filters
    selected_event_id = request.GET.get('event')
    per_page = int(request.GET.get('per_page', 25))
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('search', '').strip()

    # Init fallbacks
    registrations = Registration.objects.none()
    athletes = Athlete.objects.none()
    option_keys = []
    paginator = None
    selected_event = None

    if selected_event_id:
        try:
            selected_event = events.get(id=selected_event_id)
            registrations = selected_event.registrations.select_related().all()

            athletes_qs = Athlete.objects.filter(
                registration__event=selected_event
            ).select_related('registration', 'race', 'package')

            # Apply search if needed
            if search_query:
                athletes_qs = athletes_qs.filter(
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query) |
                    Q(email__icontains=search_query)
                )

            # Collect all option keys from selected_options JSON
            option_key_set = set()
            for athlete in athletes_qs:
                if isinstance(athlete.selected_options, dict):
                    option_key_set.update(athlete.selected_options.keys())
            option_keys = sorted(option_key_set)

            # Paginate
            paginator = Paginator(athletes_qs, per_page)
            athletes = paginator.get_page(page_number)

        except Event.DoesNotExist:
            selected_event = None

    context = {
        'events': events,
        'selected_event_id': selected_event_id,
        'selected_event': selected_event,
        'registrations': registrations,
        'athletes': athletes,
        'paginator': paginator,
        'per_page': per_page,
        'per_page_choices': [10, 25, 50, 100],
        'search_query': search_query,
        'option_keys': option_keys,
    }
    return render(request, 'dashboard/registrations.html', context)