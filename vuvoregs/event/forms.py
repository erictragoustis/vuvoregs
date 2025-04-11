"""Forms for handling event registration, athlete data entry, and special pricing logic."""  # noqa: E501

# Standard Django form imports
from cities_light.models import City, Country, Region
from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

# Project-specific models
from .models import Athlete, Event, PickUpPoint, RaceSpecialPrice, Registration


class BillingForm(forms.Form):  # noqa: D101
    billing_first_name = forms.CharField(max_length=100)
    billing_last_name = forms.CharField(max_length=100)
    billing_address_1 = forms.CharField(max_length=255)
    billing_address_2 = forms.CharField(max_length=255, required=False)
    billing_postcode = forms.CharField(max_length=20)
    billing_country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        widget=forms.Select(attrs={"class": "form-select", "id": "billing-country"}),
    )
    billing_region = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "id": "billing-region"}),
        required=False,
    )
    billing_city = forms.ModelChoiceField(
        queryset=City.objects.none(),
        widget=forms.Select(attrs={"class": "form-select", "id": "billing-city"}),
    )
    billing_phone = forms.CharField(max_length=20)
    billing_email = forms.EmailField()


class AthleteForm(forms.ModelForm):
    """Form for capturing individual athlete data during race registration."""

    class Meta:
        """Metadata for AthleteForm, defining model, fields, and widgets."""

        model = Athlete
        fields = [
            "first_name",
            "last_name",
            "team",
            "email",
            "phone",
            "sex",
            "dob",
            "pickup_point",
            "hometown",
            "package",
            "special_price",
        ]

        widgets = {
            "dob": forms.DateInput(
                format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}
            )
        }

    def __init__(self, *args, **kwargs):
        """Initialize the AthleteForm with optional race and packages context.

        Parameters
        ----------
        *args : tuple
            Positional arguments for the form.
        **kwargs : dict
            Keyword arguments for the form, including 'race' and 'packages'.
        """
        race = kwargs.pop("race", None)
        packages = kwargs.pop("packages", None)
        super().__init__(*args, **kwargs)

        self.request = None
        self.form_index = None
        self.race = race
        if race:
            self.fields["special_price"] = forms.ModelChoiceField(
                queryset=RaceSpecialPrice.objects.filter(race=race),
                required=False,
                label="Special Price (if applicable)",
                widget=forms.RadioSelect,
            )

        # 🔁 Limit package options
        if packages is not None:
            self.fields["package"].queryset = packages
        self.fields["package"].required = True
        self.fields["package"].error_messages = {"required": "Please select a package."}

        # 🎯 Limit pickup points to event
        if race:
            self.fields["pickup_point"].queryset = race.event.pickup_points.all()
        else:
            self.fields["pickup_point"].queryset = PickUpPoint.objects.none()

    def clean(self):
        """Validate form data, enforce T&Cs, extract selected options and special prices."""  # noqa: E501
        cleaned_data = super().clean()

        if not cleaned_data.get("package"):
            self.add_error("package", "You must select a package.")

        # 🧠 Extract selected package options from request POST
        if self.request and self.form_index is not None:
            prefix = "athlete"
            index = self.form_index

            selected_options = {}
            for key in self.request.POST:
                if key.startswith(f"{prefix}-{index}-option-") and not key.endswith(
                    "-name"
                ):
                    option_id = key.split(f"{prefix}-{index}-option-")[-1]
                    option_name_key = f"{key}-name"
                    option_name = self.request.POST.get(
                        option_name_key, f"Option {option_id}"
                    )
                    values = self.request.POST.getlist(key)
                    if values and any(v.strip() for v in values):
                        selected_options[option_name] = values
            self.instance.selected_options = (
                selected_options if selected_options else {}
            )
        print("🧼 CLEANED:", cleaned_data)
        print("🧾 ERRORS:", self.errors)
        return cleaned_data


class MinParticipantsFormSet(BaseInlineFormSet):
    """Formset enforcing minimum participant count on a race."""

    def __init__(self, *args, **kwargs):
        """Initialize the formset with race context.

        Parameters
        ----------
        *args : tuple
            Positional arguments for the formset.
        **kwargs : dict
            Keyword arguments for the formset, including 'race'.
        """
        self.race = kwargs.pop("race", None)
        super().__init__(*args, **kwargs)

    def add_fields(self, form, index):
        """Add additional fields to the form in the formset.

        Parameters
        ----------
        form : forms.Form
            The form to which additional fields are added.
        index : int
            The index of the form in the formset.
        """
        super().add_fields(form, index)
        form.empty_permitted = False
        form.request = getattr(self, "request", None)
        form.form_index = index
        form.race = self.race

    def clean(self):
        """Ensure the minimum number of participants is met."""
        super().clean()
        if self.race and self.race.min_participants:
            filled_forms = sum(
                1
                for form in self.forms
                if form.has_changed() and not form.cleaned_data.get("DELETE", False)
            )
            if filled_forms < self.race.min_participants:
                raise ValidationError(
                    f"This race requires at least {self.race.min_participants} participants."  # noqa: E501
                )


def athlete_formset_factory(race):
    """Factory for generating an AthleteFormSet tied to a Registration.

    Adds race context and sets form count based on race's min_participants.
    """
    extra_forms = race.min_participants if race and race.min_participants else 1
    AthleteFormSet = inlineformset_factory(
        parent_model=Registration,
        model=Athlete,
        form=AthleteForm,
        formset=MinParticipantsFormSet,
        extra=extra_forms,
        can_delete=False,
    )
    return AthleteFormSet


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
