from django import forms
from django.forms import inlineformset_factory
from .models import Athlete, Registration, RacePackage

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
        if self.data:
            package_id = self.data.get(self.prefix + '-package')
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

AthleteFormSet = inlineformset_factory(
    Registration, Athlete, form=AthleteForm, extra=1, can_delete=True
)