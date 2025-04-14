"""This module contains admin views for handling athlete data.

It includes functionalities for importing bib numbers and exporting athlete data
for specific events in CSV format.
"""

import csv
from io import TextIOWrapper

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render

from event.forms import (
    BibNumberImportForm,
    ExportEventAthletesForm,
)
from event.models import Athlete


def import_bibs_view(request):
    """Handle the import of bib numbers for athletes.

    Parameters
    ----------
    request : HttpRequest
        The HTTP request object containing form data and uploaded files.

    Returns,
    -------
    HttpResponse
        A rendered HTML form or a redirect to the admin index after processing.
    """
    form = BibNumberImportForm()
    success, failed = 0, 0
    if request.method == "POST":
        form = BibNumberImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["csv_file"]
            reader = csv.DictReader(
                TextIOWrapper(file, encoding="utf-8"), delimiter=";"
            )
            for row in reader:
                athlete_id = row.get("id")
                bib = row.get("bib_number")
                try:
                    athlete = Athlete.objects.get(id=athlete_id)
                    athlete.bib_number = bib
                    athlete.save()
                    success += 1
                except Athlete.DoesNotExist:
                    failed += 1
            messages.success(request, f"{success} bib numbers updated.")
            if failed:
                messages.warning(
                    request, f"{failed} rows failed (no matching Athlete ID)."
                )
            return redirect("admin:index")
    return render(
        request, "admin/import_bibs.html", {"form": form, "title": "Import Bib Numbers"}
    )


def export_athletes_view(request):
    """Handle the export of athletes for a specific event.

    Parameters
    ----------
    request : HttpRequest
        The HTTP request object containing form data.

    Returns,
    -------
    HttpResponse
        A CSV file response containing athlete data or a rendered HTML form.
    """
    form = ExportEventAthletesForm()
    if request.method == "POST":
        form = ExportEventAthletesForm(request.POST)
        if form.is_valid():
            event = form.cleaned_data["event"]
            athletes = Athlete.objects.filter(race__event=event).select_related(
                "package", "race"
            )
            response = HttpResponse(content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = (
                f"attachment; filename=athletes_{event.name or event.id}.csv"
            )
            response.write("\ufeff")  # UTF-8 BOM for Excel
            writer = csv.writer(response, delimiter=";")
            writer.writerow([
                "id",
                "first_name",
                "last_name",
                "dob",
                "package",
                "race",
                "pickup_point",
                "bib_number",
            ])
            for athlete in athletes:
                writer.writerow([
                    athlete.id,
                    athlete.first_name,
                    athlete.last_name,
                    athlete.dob,
                    athlete.package.name if athlete.package else "",
                    athlete.race.name if athlete.race else "",
                    athlete.pickup_point.name if athlete.pickup_point else "",
                    athlete.bib_number or "",
                ])
            return response
    return render(
        request,
        "admin/export_athletes.html",
        {"form": form, "title": "Export Event Athletes"},
    )
