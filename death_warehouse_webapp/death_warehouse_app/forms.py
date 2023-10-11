from django import forms
from .models import RecherchePatient

class RecherchePatientForm(forms.ModelForm):
    class Meta:
        model = RecherchePatient
        fields = '__all__'
