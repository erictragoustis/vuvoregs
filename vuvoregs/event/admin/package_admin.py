from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from modeltranslation.translator import TranslationOptions, register

from event.models.package import PackageOption, RacePackage


class RacePackageOptionInline(admin.TabularInline):
    model = PackageOption
    extra = 1


@register(RacePackage)
class RacePackageTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@admin.register(RacePackage)
class RacePackageAdmin(TranslationAdmin):
    list_display = ("name", "event", "price_adjustment", "visible_until")
    list_filter = ("event",)
    search_fields = ("name", "event__name")
    ordering = ("event", "name")
    inlines = [RacePackageOptionInline]
