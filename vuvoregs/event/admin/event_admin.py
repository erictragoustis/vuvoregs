from django.contrib import admin, messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from modeltranslation.admin import TranslationAdmin
from modeltranslation.translator import TranslationOptions, register
from openpyxl import load_workbook

from event.models import Athlete, Race, RacePackage, Registration
from event.models.event import Event, PickUpPoint


@register(Event)
class EventTranslationOptions(TranslationOptions):
    fields = ("name", "location", "description")


@admin.register(Event)
class EventAdmin(TranslationAdmin):
    list_display = ("name", "date", "location", "is_available")
    list_filter = ("is_available",)
    search_fields = ("name", "location")
    ordering = ("-date",)
    change_form_template = "admin/event/change_form_with_download.html"


@admin.register(PickUpPoint)
class PickUpPointAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "address", "working_hours")
    list_filter = ("event",)
    search_fields = ("name", "address", "event__name")
