"""URL configuration for event-related views.

Includes routes for:
- Listing all upcoming events
- Viewing races associated with a selected event
"""

from django.urls import path

from event.views import event_list, race_list
from event.views.events import (
    countdown_timer_partial,
    event_list_partial,
    race_cards_partial,
)

app_name = "event"

urlpatterns = [
    path(
        "",
        event_list,
        name="event_list",
    ),
    path(
        "event/<int:event_id>/races/",
        race_list,
        name="race_list",
    ),
    path("htmx/events/", event_list_partial, name="htmx_event_list"),
    path(
        "htmx/countdown/<int:event_id>/", countdown_timer_partial, name="htmx_countdown"
    ),
    path(
        "htmx/event/<int:event_id>/races/",
        race_cards_partial,
        name="htmx_race_cards",
    ),
]
