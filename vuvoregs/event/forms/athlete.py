"""This module contains forms for managing athlete data during registration.

It includes:
- AthleteForm: A form for capturing individual athlete details.
- MinParticipantsFormSet: A formset enforcing minimum participant count.
- athlete_formset_factory: A factory for generating AthleteFormSet
tied to a Registration.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from event.models.athlete import Athlete
from event.models.event import PickUpPoint
from event.models.package import RaceSpecialPrice
from event.models.registration import Registration


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
