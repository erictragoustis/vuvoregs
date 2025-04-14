from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from modeltranslation.translator import TranslationOptions, register

from event.models.package import RaceSpecialPrice
from event.models.race import Race, RaceType, TimeBasedPrice


class TimeBasedPriceInline(admin.TabularInline):
    model = TimeBasedPrice
    extra = 1


class RaceSpecialPriceInline(admin.TabularInline):
    model = RaceSpecialPrice
    extra = 1


@register(Race)
class RaceTranslationOptions(TranslationOptions):
    fields = ("name",)


@admin.register(Race)
class RaceAdmin(TranslationAdmin):
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
    fields = ("name", "description")


@admin.register(RaceType)
class RaceTypeAdmin(TranslationAdmin):
    list_display = ("name",)
    search_fields = ("name",)
