"""Forms for managing event-related functionalities in the admin interface.

This module includes:
- BibNumberImportForm: For uploading a CSV to import bib numbers for athletes.
- ExportEventAthletesForm: For selecting an event to export athlete registrations.
"""

from django import forms

from event.models.event import Event


class BibNumberImportForm(forms.Form):
    """Form for uploading a CSV to import bib numbers for athletes."""

    csv_file = forms.FileField(
        label="CSV file",
        help_text="Upload a CSV with columns: id;bib_number",
        required=True,
    )


class ExportEventAthletesForm(forms.Form):
    """Form to select an event for exporting its athlete registrations."""

    event = forms.ModelChoiceField(
        queryset=Event.objects.all(), required=True, label="Select Event"
    )


class TeamExcelUploadForm(forms.Form):
    """Form for uploading an Excel file containing team data.

    This form allows admins to upload an Excel file (.xlsx) with team details.
    Ensure the file uses the provided template and that race_name and package_name match exactly.
    """

    excel_file = forms.FileField(
        label="Upload Excel File (.xlsx)",
        help_text="Use the downloaded template and make sure race_name and package_name match exactly.",
    )
