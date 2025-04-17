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
    """Form for capturing a single athlete's data during registration."""

    class Meta:
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
            # ❌ Don't include "role" here — we inject it conditionally if needed
        ]
        widgets = {
            "dob": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "form-control"},
            )
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
        self.race = kwargs.pop("race", None)
        super().__init__(*args, **kwargs)

        self.request = None
        self.formIndex = None

        if self.race:
            self.instance.race = self.race
            self.populatePackageField()
            self.populateRoleField()
            self.populateSpecialPrices()
            self.filterPickupPoints()

        self.fields["package"].required = False
        self.fields["package"].error_messages = {
            "required": _("Please select a package.")
        }

    def populatePackageField(self):
        """Populate package queryset and preselect the only available package if applicable."""
        packages_data = self.race.get_packages_with_prices()

        # Defensive: extract packages that exist
        available_packages = [
            d["package"]
            for d in packages_data
            if "package" in d and d["package"] is not None
        ]
        print("📦 Available package count:", len(packages_data))
        print("📦 Extracted packages:", available_packages)

        # Set field queryset
        self.fields["package"].queryset = RacePackage.objects.filter(
            id__in=[pkg.id for pkg in available_packages]
        )
        self.sortedPackages = packages_data

        # Auto-select if only one package
        if len(available_packages) == 1:
            self.initial["package"] = available_packages[0]

    def populateRoleField(self):
        """Dynamically inject the role field only if needed."""
        if not self.race or not self.race.requires_roles():
            return

        allowed_roles = self.race.get_allowed_roles()
        if allowed_roles.exists():
            self.fields["role"] = forms.ModelChoiceField(
                queryset=allowed_roles,
                required=True,
                label=_("Role"),
                help_text=_("Select the role this athlete will perform."),
            )

    def populateSpecialPrices(self):
        """Inject optional special price field if defined on race."""
        specials = RaceSpecialPrice.objects.filter(race=self.race)
        if specials.exists():
            self.fields["special_price"] = ModelChoiceField(
                queryset=specials,
                required=False,
                label=_("Special Price (optional)"),
                widget=RadioSelect,
            )
            self.fields["special_price"].choices = [("", _("No discount"))] + list(
                self.fields["special_price"].choices
            )
        else:
            self.fields.pop("special_price", None)

    def filterPickupPoints(self):
        """Filter pickup points to match the current event only."""
        self.fields["pickup_point"].queryset = self.race.event.pickup_points.all()

    def setRequestAndIndex(self, request, index):
        """Used by formset to pass request context for option parsing."""
        self.request = request
        self.formIndex = index

    def clean(self):
        """Parse dynamic package options from POST data."""
        cleaned_data = super().clean()
        if "role" not in cleaned_data and "role" in self.initial:
            cleaned_data["role"] = self.initial["role"]
        package = cleaned_data.get("package")

        if not package:
            self.add_error("package", _("You must select a package."))

        if self.request and self.formIndex is not None:
            selected_options = {}
            prefix = "athlete"
            index = self.formIndex

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

            self.instance.role = self.cleaned_data.get("role") or self.initial.get(
                "role"
            )

        return cleaned_data


class MinParticipantsFormSet(BaseInlineFormSet):
    """Custom formset that enforces.

    - minimum number of participants
    - valid roles if the race requires them
    """

    def __init__(self, *args, **kwargs):
        self.race = kwargs.pop("race", None)
        super().__init__(*args, **kwargs)
        self.request = None

    def setRequest(self, request):
        """Attach the request to each form (used for parsing selected package options)."""
        self.request = request

    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.empty_permitted = False
        form.setRequestAndIndex(self.request, index)
        form.race = self.race

        if self.race and self.race.requires_roles():
            allowed_roles = list(self.race.get_allowed_roles())

            if allowed_roles:
                # Add the field if not already present
                if "role" not in form.fields:
                    form.fields["role"] = ModelChoiceField(
                        queryset=self.race.get_allowed_roles(),
                        required=True,
                        label=_("Role"),
                        help_text=_("Select the role this athlete will perform."),
                    )

                # Preassign role based on form index
                role_index = index % len(allowed_roles)
                selected_role = allowed_roles[role_index]
                form.initial["role"] = selected_role

                # Ensure role is treated as submitted even if disabled
                form.data = form.data.copy()
                form.data[f"{form.prefix}-role"] = selected_role.pk

                # Make field visually readonly
                form.fields["role"].disabled = True
                form.fields["role"].widget.attrs["readonly"] = True
                form.fields["role"].widget.attrs["data-locked"] = "true"

    def clean(self):
        """Enforce minimum participants and required roles (if race type uses them)."""
        super().clean()

        if not self.race:
            return

        valid_forms = [
            form
            for form in self.forms
            if form.has_changed() and not form.cleaned_data.get("DELETE", False)
        ]

        # 🔒 Role validation
        if self.race.requires_roles():
            required_roles = list(self.race.get_allowed_roles())
            provided_roles = set()

            for form in valid_forms:
                role = form.cleaned_data.get("role")
                if not role:
                    role = form.initial.get("role")
                if role:
                    provided_roles.add(role)

            # ✅ Moved outside loop
            print("👉 Required roles:", [str(r) for r in required_roles])
            print(
                "👉 Provided roles (cleaned or initial):",
                [str(r) for r in provided_roles],
            )

            missing_roles = [
                role for role in required_roles if role not in provided_roles
            ]

            if missing_roles:
                print("❌ Missing roles:", [str(r) for r in missing_roles])
                raise ValidationError(
                    _("The following roles must be assigned: %(roles)s.")
                    % {"roles": ", ".join(str(r) for r in missing_roles)}
                )

        # 🧮 Minimum participants
        min_required = self.race.race_type.min_participants
        if min_required and len(valid_forms) < min_required:
            raise ValidationError(
                _("This race requires at least %(min)d participants.")
                % {"min": min_required}
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
