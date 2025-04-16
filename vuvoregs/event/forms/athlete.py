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
from event.models.package import RacePackage, RaceSpecialPrice
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
        """Initialize the form with dynamic context from the registration view."""
        race = kwargs.pop("race", None)
        kwargs.pop("packages", None)  # safe discard
        super().__init__(*args, **kwargs)

        self.request = None
        self.form_index = None
        self.race = race

        if race:
            self.instance.race = race

            # 🧠 Sorted + priced packages from model
            priced_packages = race.get_priced_packages()
            self.fields["package"].queryset = RacePackage.objects.filter(
                id__in=[pkg.id for pkg in priced_packages]
            )
            self.sorted_packages = priced_packages  # exposed for template

            # 🎯 Role field if the race type requires it
        if race and race.requires_roles():
            self.fields["role"] = forms.ModelChoiceField(
                queryset=race.get_allowed_roles(),
                required=True,
                label=_("Role"),
                help_text=_("Select the role this athlete will perform."),
            )

            # 🎯 Optional special price radio field
            special_prices = RaceSpecialPrice.objects.filter(race=race)
            if special_prices.exists():
                self.fields["special_price"] = ModelChoiceField(
                    queryset=special_prices,
                    required=False,
                    label=_("Special Price (optional)"),
                    widget=RadioSelect,
                )
                self.fields["special_price"].choices = [("", _("No discount"))] + list(
                    self.fields["special_price"].choices
                )
            else:
                self.fields.pop("special_price", None)

            # 🧭 Pickup points filtered to current event
            self.fields["pickup_point"].queryset = race.event.pickup_points.all()
        else:
            self.fields["pickup_point"].queryset = PickUpPoint.objects.none()

        self.fields["package"].required = True
        self.fields["package"].error_messages = {
            "required": _("Please select a package.")
        }

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
        super().add_fields(form, index)
        form.empty_permitted = False
        form.request = getattr(self, "request", None)
        form.form_index = index
        form.race = self.race

        # 🧠 Force role field logic to re-run
        if self.race and self.race.requires_roles():
            if "role" not in form.fields:
                form.fields["role"] = forms.ModelChoiceField(
                    queryset=self.race.get_allowed_roles(),
                    required=True,
                    label=_("Role"),
                    help_text=_("Select the role this athlete will perform."),
                )

    def clean(self):
        """Validate number of participants and required roles."""
        super().clean()

        if not self.race:
            return

        # ✅ Get valid athlete forms (not marked for deletion, have changes)
        filled_forms = [
            form
            for form in self.forms
            if form.has_changed() and not form.cleaned_data.get("DELETE", False)
        ]

        # Enforce required roles if race demands it
        if self.race.requires_roles():
            required_roles = list(self.race.get_allowed_roles())
            provided_roles = {form.cleaned_data.get("role") for form in filled_forms}
            missing_roles = [
                role for role in required_roles if role not in provided_roles
            ]

            if missing_roles:
                raise ValidationError(
                    _("The following roles must be assigned: %(roles)s.")
                    % {"roles": ", ".join(str(role) for role in missing_roles)}
                )
            print("DEBUG filled forms:", filled_forms)
            print(
                "DEBUG cleaned roles:",
                [f.cleaned_data.get("role") for f in filled_forms],
            )
            print("DEBUG all form errors:", [f.errors for f in self.forms])

        #  Enforce total min participants (from race_type)
        if self.race.race_type.min_participants:
            if len(filled_forms) < self.race.race_type.min_participants:
                raise ValidationError(
                    _("This race requires at least %(min)d participants.")
                    % {"min": self.race.race_type.min_participants}
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
