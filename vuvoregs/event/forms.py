from django import forms
from .models import Athlete

class AthleteRegistrationForm(forms.ModelForm):
    """Form for registering an athlete."""
    class Meta:
        model = Athlete
        fields = ['first_name', 'last_name', 'email', 'phone', 'age', 'sex', 'hometown']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
            'hometown': forms.TextInput(attrs={'class': 'form-control'}),
        }
