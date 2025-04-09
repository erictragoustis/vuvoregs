"""URL configuration for the admin views of the 'event' app.

This module defines URL patterns for administrative tasks such as importing bibs
and exporting athlete data. These views are used to manage event-related data
through the admin interface.
"""

from django.urls import path

from .admin import export_athletes_view, import_bibs_view

app_name = "event_admin"

urlpatterns = [
    path(
        "import-bibs/", import_bibs_view, name="import-bibs"
    ),  # URL for importing bibs
    path(
        "export-athletes/", export_athletes_view, name="export-athletes"
    ),  # URL for exporting athlete data  # noqa: E501
]
