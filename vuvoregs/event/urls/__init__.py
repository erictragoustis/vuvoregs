"""URL configuration for the event package.

This package includes URL patterns for events,
registration, payment, and AJAX functionality.
"""

from django.urls import include, path

urlpatterns = [
    path("", include("event.urls.events")),
    path("", include("event.urls.registration")),
    path("", include("event.urls.payment")),
    path("ajax/", include("event.urls.ajax")),
]
