from django import forms
from .models import RecherchePatient

class RecherchePatientForm(forms.Form):
    nom = forms.CharField(required=True, label="Nom")
    prenom = forms.CharField(required=False, label="Prénom")
    date_naiss = forms.DateField(required=True, label="Date de naissance (AAAA-MM-JJ)")

