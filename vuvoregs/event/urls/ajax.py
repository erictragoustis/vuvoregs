"""URL configuration for AJAX endpoints in the event application.

Includes routes for:
- Dynamically loading regions and cities (billing form)
- Fetching package option sets
- Fetching race-specific special prices
"""

from django.urls import path

from event.views import (
    load_cities,
    load_regions,
    package_options,
    special_price_options,
)

app_name = "ajax"

urlpatterns = [
    path(
        "race/package/<int:package_id>/options/",
        package_options,
        name="package_options",
    ),
    path(
        "race/<int:race_id>/special-prices/",
        special_price_options,
        name="special_price_options",
    ),
    path(
        "load-regions/",
        load_regions,
        name="ajax_load_regions",
    ),
    path(
        "load-cities/",
        load_cities,
        name="ajax_load_cities",
    ),
]
