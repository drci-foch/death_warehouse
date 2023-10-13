from django import forms


class DateInput(forms.DateInput):
    input_type = 'date'


class RecherchePatientForm(forms.Form):
    nom = forms.CharField(required=True, label="Nom")
    prenom = forms.CharField(required=False, label="Prénom")
    date_naiss = forms.DateField(
        required=True,
        label="Date de naissance",
        # Specify the attribute directly just to be sure
        widget=DateInput(attrs={'type': 'date'})
    )


class ImportFileForm(forms.Form):
    file = forms.FileField(label='Sélectionnez un fichier')
