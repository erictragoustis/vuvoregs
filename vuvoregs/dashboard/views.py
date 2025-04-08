from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from event.models import Event, Registration, Athlete
from django.db.models import Q
from django.core.paginator import Paginator
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.db.models import Count
import json
from django.utils.timezone import now, timedelta
from django.http import JsonResponse

@staff_member_required
def dashboard_home(request):
    if request.user.is_staff:
        events = Event.objects.all()
    else:
        events = Event.objects.filter(organizer=request.user)

    registrations = Registration.objects.filter(event__in=events)
    today = now().date()
    seven_days_ago = today - timedelta(days=7)

    # Summary stats
    context = {
        'total_regs': registrations.count(),
        'today_regs': registrations.filter(created_at__date=today).count(),
        'last_7_days_regs': registrations.filter(created_at__date__gte=seven_days_ago).count(),
        'upcoming_events': events.filter(date__gte=today).order_by('date')
    }

    return render(request, 'dashboard/home.html', context)

@staff_member_required
def event_dashboard(request, event_id):
    if request.user.is_staff:
        event = get_object_or_404(Event, id=event_id)
    else:
        event = get_object_or_404(Event, id=event_id, organizer=request.user)

    race_id = request.GET.get('race')
    interval = request.GET.get('interval', 'daily')  # daily, weekly, monthly
    cumulative = request.GET.get('cumulative') == 'on'

    # Choose aggregation function
    if interval == 'weekly':
        trunc_fn = TruncWeek
    elif interval == 'monthly':
        trunc_fn = TruncMonth
    else:
        trunc_fn = TruncDate

    athlete_qs = Athlete.objects.filter(registration__event=event)

    if race_id:
        athlete_qs = athlete_qs.filter(race__id=race_id)

    registrations = event.registrations.all()
    total_regs = registrations.count()
    paid_regs = registrations.filter(payment_status='paid').count()
    unpaid_regs = total_regs - paid_regs
    total_athletes = athlete_qs.count()

    # Chart data
    chart_qs = (
        athlete_qs
        .annotate(date_group=trunc_fn('registration__created_at'))
        .values('date_group')
        .annotate(count=Count('id'))
        .order_by('date_group')
    )

    labels = []
    counts = []
    running_total = 0
    for entry in chart_qs:
        date_label = entry['date_group'].strftime('%Y-%m-%d')
        labels.append(date_label)
        running_total += entry['count']
        counts.append(running_total if cumulative else entry['count'])

    context = {
        'event': event,
        'total_regs': total_regs,
        'paid_regs': paid_regs,
        'unpaid_regs': unpaid_regs,
        'total_athletes': total_athletes,
        'chart_labels': json.dumps(labels),
        'chart_counts': json.dumps(counts),
        'races': event.races.all(),
        'selected_race_id': race_id,
        'interval': interval,
        'cumulative': cumulative,
    }

    return render(request, 'dashboard/event_dashboard.html', context)


@staff_member_required
def registration_list(request):
    # Get events for admin or specific organizer
    if request.user.is_staff:
        events = Event.objects.all()
    else:
        events = Event.objects.filter(organizer=request.user)

    # Query params
    selected_event_id = request.GET.get('event')
    per_page = int(request.GET.get('per_page', 25))
    page_number = request.GET.get('page', 1)
    search_query = request.GET.get('search', '').strip()
    race_id = request.GET.get('race')
    package_id = request.GET.get('package')

    # Init data
    registrations = Registration.objects.none()
    athletes = Athlete.objects.none()
    option_keys = []
    paginator = None
    selected_event = None
    races = []
    packages = []

    if selected_event_id:
        try:
            selected_event = events.get(id=selected_event_id)
            registrations = selected_event.registrations.select_related().all()

            athletes_qs = Athlete.objects.filter(
                registration__event=selected_event
            ).select_related('registration', 'race', 'package')

            # Apply search
            if search_query:
                athletes_qs = athletes_qs.filter(
                    Q(first_name__icontains=search_query) |
                    Q(last_name__icontains=search_query) |
                    Q(email__icontains=search_query)
                )

            # Apply race/package filters
            if race_id:
                athletes_qs = athletes_qs.filter(race__id=race_id)

            if package_id:
                athletes_qs = athletes_qs.filter(package__id=package_id)

            # Extract option keys for dynamic columns
            option_key_set = set()
            for athlete in athletes_qs:
                if isinstance(athlete.selected_options, dict):
                    option_key_set.update(athlete.selected_options.keys())
            option_keys = sorted(option_key_set)

            # Paginate
            paginator = Paginator(athletes_qs, per_page)
            athletes = paginator.get_page(page_number)

            # Get races & packages for filter dropdowns
            races = selected_event.races.all()
            packages = selected_event.packages.all()

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
        'race_id': race_id,
        'package_id': package_id,
        'races': races,
        'packages': packages,
    }
    return render(request, 'dashboard/registrations.html', context)

@staff_member_required
def event_chart_data(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    race_id = request.GET.get('race')
    interval = request.GET.get('interval', 'daily')
    cumulative = request.GET.get('cumulative') == 'true'

    # Aggregation function
    trunc_fn = TruncDate if interval == 'daily' else TruncWeek if interval == 'weekly' else TruncMonth

    athletes = Athlete.objects.filter(registration__event=event)
    if race_id:
        athletes = athletes.filter(race__id=race_id)

    chart_qs = (
        athletes
        .annotate(date_group=trunc_fn('registration__created_at'))
        .values('date_group')
        .annotate(count=Count('id'))
        .order_by('date_group')
    )

    labels = []
    counts = []
    total = 0
    for entry in chart_qs:
        labels.append(entry['date_group'].strftime('%Y-%m-%d'))
        total += entry['count']
        counts.append(total if cumulative else entry['count'])

    return JsonResponse({
        'labels': labels,
        'counts': counts
    })