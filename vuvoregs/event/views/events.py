# Built-in libraries

# Django core imports
from django.shortcuts import render

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
    """Display the races associated with a specific event.

    If the event doesn't exist, show an appropriate message.
    """
    try:
        event = Event.objects.get(pk=event_id)
        races = Race.objects.filter(event=event)
    except Event.DoesNotExist:
        return render(
            request,
            "registration/race_list.html",
            {
                "event": None,
                "races": [],
                "message": "Registrations are closed for this event.",
            },
        )
    return render(
        request,
        "registration/race_list.html",
        {
            "event": event,
            "races": races,
        },
    )
