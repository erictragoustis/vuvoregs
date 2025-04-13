"""Public views for listing events and races available for registration."""

from django.shortcuts import get_object_or_404, render

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
        .select_related("race_type")  # useful for __str__ and display
        .prefetch_related(
            "packages",  # show available packages for this race
            "packages__races",  # used by pricing methods on the package
            "packages__packageoption_set",  # options like T-shirt size
            "time_based_prices",  # time-based pricing
        )
    )

    return render(
        request,
        "registration/race_list.html",
        {
            "event": event,
            "races": races,
        },
    )
