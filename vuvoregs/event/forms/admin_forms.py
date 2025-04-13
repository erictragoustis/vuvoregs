"""Forms for managing event-related functionality in the admin interface.

Includes:
- BibNumberImportForm: For importing bib numbers from a CSV.
- ExportEventAthletesForm: For selecting and exporting event registrations.
- TeamExcelUploadForm: For uploading team registration data via Excel.
"""

from django import forms

from event.models.event import Event


class BibNumberImportForm(forms.Form):
    """Upload a CSV file to assign or update bib numbers for athletes.

    Expected format:
        id;bib_number
    """

    csv_file = forms.FileField(
        label="CSV File",
        help_text="Upload a CSV file with two columns: id;bib_number",
        required=True,
    )


class ExportEventAthletesForm(forms.Form):
    """Select an event to export all associated athlete registrations.

    Used for CSV or Excel report generation.
    """

    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        required=True,
        label="Select Event",
    )


class TeamExcelUploadForm(forms.Form):
    """Upload an Excel file with team registration details.

    Expected format:
        - One sheet
        - Must match the official template (race_name, package_name required)
    """

    excel_file = forms.FileField(
        label="Upload Excel File (.xlsx)",
        help_text=(
            "Use the provided template. "
            "Ensure that race_name and package_name match exactly."
        ),
        required=True,
    )
