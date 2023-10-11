from django import forms
from .models import RecherchePatient

class RecherchePatientForm(forms.Form):
    nom = forms.CharField(required=True, label="Nom")
    prenom = forms.CharField(required=True, label="Prénom")
    date_naiss = forms.DateField(required=True, label="Date de naissance")


    def rechercher_patients(self):
        # Récupérez les données du formulaire
        nom = self.cleaned_data.get('nom')
        prenom = self.cleaned_data.get('prenom')
        date_naiss = self.cleaned_data.get('date_naiss')

        patients = RecherchePatient.objects.filter(
        nom=nom,
        date_naiss=date_naiss,
        prenomicontains=prenom 
        ).distinct()



        return patients
