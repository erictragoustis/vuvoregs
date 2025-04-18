"""Public views for listing events and races available for registration."""

from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from event.models import Event, Race


def event_list(request):
    """Display a list of upcoming events, sorted by date.

    Template:
        registration/event_list.html

    Context:
        events (QuerySet): All upcoming events ordered by date.
    """
    events = Event.objects.order_by("date")
    return render(request, "registration/event_list.html", {"events": events})


def race_list(request, event_id):
    """Display all races for a specific event, including related packages.

    Template:
        registration/race_list.html

    Context:
        event (Event): Selected event instance.
        races (QuerySet): All Race objects linked to the event, with packages.
    """
    event = get_object_or_404(Event, pk=event_id)

    races = (
        Race.objects.filter(event=event)
        .select_related("race_type")
        .prefetch_related("packages", "special_prices")
    )

    return render(
        request,
        "registration/race_list.html",
        {
            "event": event,
            "races": races,
        },
    )


def event_list_partial(request):
    """HTMX view to return the event cards only (used for dynamic refresh)."""
    events = Event.objects.order_by("date")
    return render(request, "registration/partials/event_cards.html", {"events": events})


def countdown_timer_partial(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    now = timezone.now()
    remaining = event.registration_end_date - now

    if remaining.total_seconds() > 0:
        days = remaining.days
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
    else:
        days = hours = minutes = 0

    return render(
        request,
        "registration/partials/countdown_timer.html",
        {"event": event, "days": days, "hours": hours, "minutes": minutes},
    )


def race_cards_partial(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    races = event.races.all()
    return render(request, "registration/partials/race_cards.html", {"races": races})
