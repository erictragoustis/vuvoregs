# ✅ Refined AthleteForm with error integration into universal toast system
# Non-field errors will be collected by the template and shown as toasts

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from .models import Athlete, Registration, RacePackage, PickUpPoint

# 🏃 Form for registering a single athlete
class AthleteForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = [
            'first_name', 'last_name', 'email', 'phone',
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

        # Injected later via formset
        self.request = None
        self.form_index = None

        # Set packages for dropdown and mark as required
        if packages is not None:
            self.fields['package'].queryset = packages

        self.fields['package'].required = True
        self.fields['package'].error_messages = {
            'required': 'Please select a package.'
        }

        # Filter pickup points based on event from race
        if race:
            event = race.event
            self.fields['pickup_point'].queryset = event.pickup_points.all()
        else:
            self.fields['pickup_point'].queryset = PickUpPoint.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        # 🚨 Enforce that a package is selected
        if not cleaned_data.get('package'):
            self.add_error('package', "You must select a package.")

        # 🔌 Parse selected_options from request.POST (if request injected)
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


# 📦 Custom formset enforcing min participants and request injection
class MinParticipantsFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.race = kwargs.pop('race', None)
        super().__init__(*args, **kwargs)

    def add_fields(self, form, index):
        super().add_fields(form, index)
        # Inject request + index context to each form
        form.empty_permitted = False
        form.request = getattr(self, 'request', None)
        form.form_index = index

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


# 🧪 Factory for dynamic athlete formset per race context
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
