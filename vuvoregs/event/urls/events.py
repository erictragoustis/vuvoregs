"""URL configuration for event-related views.

This module defines URL patterns for event and race-related views.
"""

from django.urls import path

from event.views import event_list, race_list

urlpatterns = [
    path("", event_list, name="event_list"),
    path("event/<int:event_id>/races/", race_list, name="race_list"),
]
