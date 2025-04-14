import csv

from django import forms
from django.contrib import admin
from django.http import HttpResponse
from django_json_widget.widgets import JSONEditorWidget
from modeltranslation.admin import TranslationAdmin
from modeltranslation.translator import TranslationOptions, register

from event.models.athlete import Athlete


class AthleteAdminForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "package",
            "race",
            "pickup_point",
            "selected_options",
        ]
        widgets = {
            "selected_options": JSONEditorWidget(
                options={"mode": "form", "mainMenuBar": True}
            ),
        }


@register(Athlete)
class AthleteTranslationOptions(TranslationOptions):
    fields = ("hometown",)


def export_athletes_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=athletes_export.csv"
    writer = csv.writer(response, delimiter=";")
    writer.writerow([
        "id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "package",
        "race",
        "pickup_point",
        "bib_number",
    ])
    for athlete in queryset:
        writer.writerow([
            athlete.id,
            athlete.first_name,
            athlete.last_name,
            athlete.email,
            athlete.phone,
            athlete.package.name if athlete.package else "",
            athlete.race.name if athlete.race else "",
            athlete.pickup_point.name if athlete.pickup_point else "",
            athlete.bib_number or "",
        ])
    return response


@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    form = AthleteAdminForm
    ordering = ["-registration__created_at"]
    list_display = (
        "registration__created_at",
        "first_name",
        "last_name",
        "email",
        "race",
        "package",
        "pickup_point",
        "dob",
        "special_price",
        "formatted_selected_options",
    )
    list_filter = ("race__event", "race", "package", "pickup_point")
    search_fields = ("first_name", "last_name", "race__name", "email")
    readonly_fields = ["formatted_selected_options"]
    actions = [export_athletes_to_csv]
    fields = (
        "first_name",
        "last_name",
        "dob",
        "sex",
        "email",
        "phone",
        "pickup_point",
        "race",
        "package",
        "registration",
        "selected_options",
    )

    def formatted_selected_options(self, obj):
        if not obj.selected_options:
            return "-"
        try:
            return "\n".join(
                f"{k}: {', '.join(v)}" for k, v in obj.selected_options.items()
            )
        except Exception:
            return "⚠️ Invalid JSON"

    formatted_selected_options.short_description = "Package Options"
