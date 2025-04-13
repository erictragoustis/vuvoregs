"""URL configuration for event-related views.

Includes routes for:
- Listing all upcoming events
- Viewing races associated with a selected event
"""

from django.urls import path

from event.views import event_list, race_list

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
]
