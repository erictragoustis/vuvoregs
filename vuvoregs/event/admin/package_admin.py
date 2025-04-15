"""Admin configuration for managing RacePackage and related models.

This module provides:
- RacePackageAdmin: Admin interface for RacePackage with translation support.
- RacePackageOptionInline: Inline admin for PackageOption.
"""

from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from modeltranslation.translator import TranslationOptions, register

from event.models.package import PackageOption, RacePackage


class RacePackageOptionInline(admin.TabularInline):
    """Inline admin configuration for managing PackageOption models."""

    model = PackageOption
    extra = 1


@register(RacePackage)
class RacePackageTranslationOptions(TranslationOptions):
    """Translation options for the RacePackage model.

    Specifies the fields that support translations.
    """

    fields = ("name", "description")


@admin.register(RacePackage)
class RacePackageAdmin(TranslationAdmin):
    """Admin interface for the RacePackage model.

    Provides configuration for displaying, filtering, searching,
    and ordering RacePackage instances
    in the Django admin interface.
    """

    list_display = ("name", "event", "price_adjustment", "visible_until")
    list_filter = ("event",)
    search_fields = ("name", "event__name")
    ordering = ("event", "name")
    inlines = [RacePackageOptionInline]
