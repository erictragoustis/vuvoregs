"""Admin module for managing Athlete entities.

This module provides:
- AthleteAdminForm: A custom form for Athlete model.
- AthleteTranslationOptions: Translation options for Athlete fields.
- export_athletes_to_csv: A utility function to export Athlete data to CSV.
- AthleteAdmin: Admin interface for Athlete model.
"""

import csv

from django import forms
from django.contrib import admin
from django.http import HttpResponse
from django_json_widget.widgets import JSONEditorWidget
from modeltranslation.translator import TranslationOptions, register

from event.models.athlete import Athlete


class AthleteAdminForm(forms.ModelForm):
    """Custom form for managing Athlete entities in the admin interface."""

    class Meta:
        """Metadata for AthleteAdminForm specifying model and form fields."""

        model = Athlete
        fields = [
            "first_name",
            "last_name",
            "hometown",
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
    """Translation options for the Athlete model fields."""

    fields = ("hometown",)


def export_athletes_to_csv(modeladmin, request, queryset):
    """Export selected Athlete records to a CSV file.

    Parameters
    ----------
    modeladmin : ModelAdmin
        The admin interface for the Athlete model.
    request : HttpRequest
        The HTTP request object.
    queryset : QuerySet
        The queryset of selected Athlete objects.

    Returns,
    -------
    HttpResponse
        A response containing the CSV file for download.
    """
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
    """Admin interface for managing Athlete entities.

    This class customizes the admin interface for the Athlete model,
    including form configuration, list display, filters, search fields,
    and actions.
    """

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
        "hometown",
        "pickup_point",
        "race",
        "package",
        "registration",
        "selected_options",
    )

    def formatted_selected_options(self, obj):
        """Format and return the selected options for display.

        Parameters
        ----------
        obj : Athlete
            The Athlete instance whose selected options are to be formatted.

        Returns,
        -------
        str
            A formatted string of selected options or a placeholder if no options exist.
        """
        if not obj.selected_options:
            return "-"
        try:
            return "\n".join(
                f"{k}: {', '.join(v)}" for k, v in obj.selected_options.items()
            )
        except Exception:
            return "⚠️ Invalid JSON"

    formatted_selected_options.short_description = "Package Options"
