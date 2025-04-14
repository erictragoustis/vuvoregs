"""Admin module for managing events and related models in the Django admin interface.

This module includes:
- EventAdmin: Admin interface for the Event model with translation support.
- PickUpPointAdmin: Admin interface for the PickUpPoint model.
"""

from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from modeltranslation.translator import TranslationOptions, register

from event.models.event import Event, PickUpPoint


@register(Event)
class EventTranslationOptions(TranslationOptions):
    """Translation options for the Event model.

    Specifies the fields that support translations.
    """

    fields = ("name", "location", "description")


@admin.register(Event)
class EventAdmin(TranslationAdmin):
    """Admin interface for the Event model.

    Provides functionality for managing events in the Django admin interface,
    including filtering, searching, and ordering.
    """

    list_display = ("name", "date", "location", "is_available")
    list_filter = ("is_available",)
    search_fields = ("name", "location")
    ordering = ("-date",)
    change_form_template = "admin/event/change_form_with_download.html"


@admin.register(PickUpPoint)
class PickUpPointAdmin(admin.ModelAdmin):
    """Admin interface for the PickUpPoint model.

    Provides functionality for managing pickup points in the Django admin interface,
    including filtering, searching, and displaying relevant fields.
    """

    list_display = ("name", "event", "address", "working_hours")
    list_filter = ("event",)
    search_fields = ("name", "address", "event__name")
