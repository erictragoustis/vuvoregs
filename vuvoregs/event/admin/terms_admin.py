from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from modeltranslation.translator import register, TranslationOptions

from event.models.terms import TermsAndConditions


@register(TermsAndConditions)
class TermsAndConditionsTranslationOptions(TranslationOptions):
    fields = ("title", "content")


@admin.register(TermsAndConditions)
class TermsAndConditionsAdmin(TranslationAdmin):
    list_display = ("event", "version", "created_at")
    search_fields = ("event__name", "version", "title")
    ordering = ("-created_at",)
