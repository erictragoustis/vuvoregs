"""Forms for managing athlete data during race registration.

Includes:
- AthleteForm: Captures individual athlete info and dynamic option logic
- MinParticipantsFormSet: Enforces race-level participant thresholds
- athlete_formset_factory: Produces an inline formset for Registration
"""

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import (
    BaseInlineFormSet,
    ModelChoiceField,
    RadioSelect,
    inlineformset_factory,
)
from django.utils.translation import gettext_lazy as _

from event.models.athlete import Athlete
from event.models.event import PickUpPoint
from event.models.package import RaceSpecialPrice
from event.models.registration import Registration


class AthleteForm(forms.ModelForm):
    """Form for capturing a single athlete's data during registration.

    Supports dynamic race packages, special prices, and pickup point selection.
    """

    class Meta:
        """Meta class to define model and form field configurations."""

        model = Athlete
        fields = [
            "first_name",
            "last_name",
            "fathers_name",
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
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "form-control"},
            ),
        }
        labels = {
            "first_name": _("First Name"),
            "last_name": _("Last Name"),
            "fathers_name": _("Father's Name"),
            "team": _("Team"),
            "email": _("Email"),
            "phone": _("Phone"),
            "sex": _("Sex"),
            "dob": _("Date of Birth"),
            "pickup_point": _("Pickup Point"),
            "hometown": _("Hometown"),
            "package": _("Package"),
            "special_price": _("Special Price"),
        }

    def __init__(self, *args, **kwargs):
        """Initialize the form with dynamic context from the registration view.

        Args:
            *args: Positional arguments passed to the parent class.
            **kwargs: Keyword arguments, including:
                race (Race): The race the athlete is registering for.
                packages (QuerySet): Available packages for the race.
        """
        race = kwargs.pop("race", None)
        packages = kwargs.pop("packages", None)
        super().__init__(*args, **kwargs)

        self.request = None
        self.form_index = None
        self.race = race

        if race:
            special_prices = RaceSpecialPrice.objects.filter(race=race)
            self.fields["special_price"] = ModelChoiceField(
                queryset=special_prices,
                required=False,
                label=_("Special Price (optional)"),
                widget=RadioSelect,
            )
            self.fields["special_price"].choices = [("", _("No discount"))] + list(
                self.fields["special_price"].choices
            )

        # Filter packages specific to the current race
        if packages is not None:
            self.fields["package"].queryset = packages

        self.fields["package"].required = True
        self.fields["package"].error_messages = {
            "required": _("Please select a package.")
        }

        # Filter pickup points to those available for the current event
        self.fields["pickup_point"].queryset = (
            race.event.pickup_points.all() if race else PickUpPoint.objects.none()
        )

    def clean(self):
        """Enrich the cleaned_data with selected package options from the POST data.

        Also validates that a package is selected and extracts dynamic options.
        """
        cleaned_data = super().clean()

        if not cleaned_data.get("package"):
            self.add_error("package", _("You must select a package."))

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

            self.instance.selected_options = selected_options or {}

        if settings.DEBUG:
            print("🧼 CLEANED:", cleaned_data)
            print("🧾 ERRORS:", self.errors)

        return cleaned_data


class MinParticipantsFormSet(BaseInlineFormSet):
    """Custom formset that enforces a race's minimum number of participants."""

    def __init__(self, *args, **kwargs):
        self.race = kwargs.pop("race", None)
        super().__init__(*args, **kwargs)

    def add_fields(self, form, index):
        """Inject race/request context and enforce completeness of each subform."""
        super().add_fields(form, index)
        form.empty_permitted = False
        form.request = getattr(self, "request", None)
        form.form_index = index
        form.race = self.race

    def clean(self):
        """Raise a validation error if fewer forms than required are submitted."""
        super().clean()

        if self.race and self.race.min_participants:
            filled_forms = sum(
                1
                for form in self.forms
                if form.has_changed() and not form.cleaned_data.get("DELETE", False)
            )
            if filled_forms < self.race.min_participants:
                raise ValidationError(
                    _("This race requires at least %(min)d participants.")
                    % {"min": self.race.min_participants}
                )


def athlete_formset_factory(race):
    """Generate a formset for entering athletes tied to a given race/registration.

    The formset includes validation for minimum participant counts.
    """
    extra_forms = race.min_participants if race and race.min_participants else 1

    return inlineformset_factory(
        parent_model=Registration,
        model=Athlete,
        form=AthleteForm,
        formset=MinParticipantsFormSet,
        extra=extra_forms,
        can_delete=False,
    )
