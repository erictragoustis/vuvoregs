"""Admin configuration for managing Race and RaceType models.

This module provides Django admin classes and translation options for:
- Race: Represents a race event with various attributes.
- RaceType: Represents the type of a race.
"""

from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from modeltranslation.translator import TranslationOptions, register

from event.models.package import RaceSpecialPrice
from event.models.race import Race, RaceType, TimeBasedPrice


class TimeBasedPriceInline(admin.TabularInline):
    """Inline admin configuration for managing TimeBasedPrice instances."""

    model = TimeBasedPrice
    extra = 1


class RaceSpecialPriceInline(admin.TabularInline):
    """Inline admin configuration for managing RaceSpecialPrice instances."""

    model = RaceSpecialPrice
    extra = 1


@register(Race)
class RaceTranslationOptions(TranslationOptions):
    """Translation options for the Race model."""

    fields = ("name",)


@admin.register(Race)
class RaceAdmin(TranslationAdmin):
    """Admin configuration for managing Race model in the Django admin interface."""

    list_display = (
        "name",
        "race_type",
        "race_km",
        "event",
        "base_price_individual",
        "base_price_team",
    )
    list_filter = ("event", "race_type")
    search_fields = ("race_type__name", "event__name")
    ordering = ("event", "race_type")
    fields = (
        "event",
        "name",
        "race_type",
        "race_km",
        "max_participants",
        "min_participants",
        "team_discount_threshold",
        "base_price_individual",
        "base_price_team",
        "image",
    )
    inlines = [TimeBasedPriceInline, RaceSpecialPriceInline]


@register(RaceType)
class RaceTypeTranslationOptions(TranslationOptions):
    """Translation options for the RaceType model."""

    fields = ("name", "description")


@admin.register(RaceType)
class RaceTypeAdmin(TranslationAdmin):
    """Admin configuration for managing RaceType model in the Django admin interface."""

    list_display = ("name",)
    search_fields = ("name",)
