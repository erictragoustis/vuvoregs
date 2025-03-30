from django import forms
from django.forms import inlineformset_factory
from .models import Athlete, Registration, RacePackage, Race
from django.core.exceptions import ValidationError

class AthleteForm(forms.ModelForm):
    class Meta:
        model = Athlete
        fields = ['first_name', 'last_name', 'email', 'phone', 'age', 'sex', 'hometown', 'package']

    def __init__(self, *args, **kwargs):
        race = kwargs.pop('race', None)
        packages = kwargs.pop('packages', None)
        super().__init__(*args, **kwargs)
        if packages:
            self.fields['package'].queryset = packages
        if self.data or not self.instance.pk:
            package_id = self.data.get(self.prefix + '-package') if self.data else None
            if self.instance.pk:
                package_id = self.instance.package_id
            if package_id:
                try:
                    package = RacePackage.objects.get(pk=package_id)
                    if package.packageoption_set.exists():
                        self.fields['selected_options'] = forms.ChoiceField(
                            choices=[(option.id, option.name) for option in package.packageoption_set.all()],
                            required=False,
                            label='Package Options'
                        )
                except RacePackage.DoesNotExist:
                    pass
        print(self.fields) #debug
        #print(self.prefix)
        #print(package_id)

class MinParticipantsFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if hasattr(self, 'race') and self.race.min_participants:
            valid_forms = 0
            for form in self:
                if form.is_valid() and form.has_changed():
                    valid_forms += 1
            if valid_forms < self.race.min_participants:
                raise ValidationError(f"A registration must have at least {self.race.min_participants} participants.")

def athlete_formset_factory(race):
    return inlineformset_factory(
        Registration, Athlete, form=AthleteForm, formset=MinParticipantsFormSet, extra=race.min_participants if race and race.min_participants else 1, can_delete=False
    )