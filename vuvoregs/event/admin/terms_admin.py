"""Admin module for managing Terms and Conditions in the event application.

This module provides:
- Translation options for TermsAndConditions model.
- Admin interface customization for TermsAndConditions model.
"""

from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from modeltranslation.translator import TranslationOptions, register

from event.models.terms import TermsAndConditions


@register(TermsAndConditions)
class TermsAndConditionsTranslationOptions(TranslationOptions):
    """Translation options for the TermsAndConditions model.

    Specifies the fields that require translation.
    """

    fields = ("title", "content")


@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(TranslationAdmin):
    """Admin interface for managing Terms and Conditions.

    Provides options for displaying, searching, and ordering Terms and Conditions
    in the admin panel.
    """

    list_display = ("event", "version", "created_at")
    search_fields = ("event__name", "version", "title")
    ordering = ("-created_at",)
