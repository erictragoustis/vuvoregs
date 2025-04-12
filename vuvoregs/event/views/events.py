# Built-in libraries

from django.db.models import Q

# Django core imports
from django.shortcuts import get_object_or_404, render

# Local app imports
from event.models import (
    Event,
    Race,
)


# 📅 List all upcoming events
def event_list(request):
    """Display a list of upcoming events sorted by date."""
    events = Event.objects.order_by("date")
    return render(request, "registration/event_list.html", {"events": events})


# 🏁 Show races under a selected event
def race_list(request, event_id):
    """Display races and visible packages for a specific event."""
    event = get_object_or_404(Event, pk=event_id)

    races = Race.objects.filter(event=event).prefetch_related(
        "packages",  # fetch RacePackage objects
        "packages__races",  # required for get_current_final_price()
        "time_based_prices",  # active pricing
    )

    return render(
        request,
        "registration/race_list.html",
        {
            "event": event,
            "races": races,
        },
    )
