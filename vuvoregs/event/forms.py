from django import forms
from django.forms import inlineformset_factory
from .models import Athlete, Registration, RacePackage, PickUpPoint
from django.core.exceptions import ValidationError

class AthleteForm(forms.ModelForm):
    """
    Form for registering an athlete to a race.
    Filters available packages and pickup points by event.
    """
    class Meta:
        model = Athlete
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'sex', 'dob', 'pickup_point', 'hometown', 'package'
        ]
        widgets = {
            'dob': forms.DateInput(
                format=('%Y-%m-%d'),
                attrs={'type': 'date', 'class': 'form-control'}
            )
        }

    def __init__(self, *args, **kwargs):
        race = kwargs.pop('race', None)
        packages = kwargs.pop('packages', None)
        super().__init__(*args, **kwargs)

        # ✅ Corrected: allow empty querysets
        if packages is not None:
            self.fields['package'].queryset = packages

        if race:
            event = race.event
            self.fields['pickup_point'].queryset = event.pickup_points.all()
        else:
            self.fields['pickup_point'].queryset = PickUpPoint.objects.none()
        
      

class MinParticipantsFormSet(forms.BaseInlineFormSet):
    """Ensures that the minimum required participants are registered."""
    def clean(self):
        super().clean()
        if hasattr(self, 'race') and self.race.min_participants:
            valid_forms = sum(1 for form in self if form.is_valid() and form.has_changed())
            if valid_forms < self.race.min_participants:
                raise ValidationError(f"A registration must have at least {self.race.min_participants} participants.")

def athlete_formset_factory(race):
    """Creates a formset for registering multiple athletes."""
    return inlineformset_factory(
        Registration, Athlete, 
        form=AthleteForm, 
        formset=MinParticipantsFormSet, 
        extra=race.min_participants if race and race.min_participants else 1, 
        can_delete=False
    )
