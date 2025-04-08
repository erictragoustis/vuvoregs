from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Event

from .models import Athlete, Registration, RacePackage, PickUpPoint


class AthleteForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = [
            'first_name', 'last_name', 'team' ,'email', 'phone',
            'sex', 'dob', 'pickup_point', 'hometown', 'package'
        ]
        widgets = {
            'dob': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            )
        }

    def __init__(self, *args, **kwargs):
        race = kwargs.pop('race', None)
        packages = kwargs.pop('packages', None)
        super().__init__(*args, **kwargs)

        self.request = None
        self.form_index = None
        self.race = race

        if packages is not None:
            self.fields['package'].queryset = packages
        self.fields['package'].required = True
        self.fields['package'].error_messages = {
            'required': 'Please select a package.'
        }

        if race:
            self.fields['pickup_point'].queryset = race.event.pickup_points.all()
        else:
            self.fields['pickup_point'].queryset = PickUpPoint.objects.none()

        # 🔐 Terms & Conditions agreement per event
        terms = getattr(race.event, 'terms', None) if race else None
        if terms:
            self.fields['agrees_to_terms'] = forms.BooleanField(
                label=f"I agree to the Terms & Conditions (v{terms.version}) for {race.event.name}",
                required=True,
                error_messages={'required': 'You must agree to the Terms & Conditions to register.'}
            )

    def clean(self):
        cleaned_data = super().clean()

        # 🔒 Enforce T&Cs requirement
        terms = getattr(self.race.event, 'terms', None)
        if terms:
            self.instance.agreed_to_terms = terms
            self.instance.agreed_at = timezone.now()
        else:
            raise ValidationError("This event has no Terms & Conditions set.")

        if not cleaned_data.get('package'):
            self.add_error('package', "You must select a package.")

        if self.request and self.form_index is not None:
            prefix = "athlete"
            index = self.form_index

            selected_options = {}
            for key in self.request.POST:
                if key.startswith(f'{prefix}-{index}-option-') and not key.endswith('-name'):
                    option_id = key.split(f'{prefix}-{index}-option-')[-1]
                    option_name_key = f'{key}-name'
                    option_name = self.request.POST.get(option_name_key, f'Option {option_id}')
                    values = self.request.POST.getlist(key)
                    if values and any(v.strip() for v in values):
                        selected_options[option_name] = values
            self.instance.selected_options = selected_options if selected_options else {}

        return cleaned_data


class MinParticipantsFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.race = kwargs.pop('race', None)
        super().__init__(*args, **kwargs)

    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.empty_permitted = False
        form.request = getattr(self, 'request', None)
        form.form_index = index
        form.race = self.race

    def clean(self):
        super().clean()
        if self.race and self.race.min_participants:
            filled_forms = sum(
                1 for form in self.forms
                if form.has_changed() and not form.cleaned_data.get('DELETE', False)
            )
            if filled_forms < self.race.min_participants:
                raise ValidationError(
                    f"This race requires at least {self.race.min_participants} participants."
                )


def athlete_formset_factory(race):
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
    csv_file = forms.FileField(
        label="CSV file",
        help_text="Upload a CSV with columns: id;bib_number",
        required=True
    )
    
class ExportEventAthletesForm(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.all(), required=True, label="Select Event")