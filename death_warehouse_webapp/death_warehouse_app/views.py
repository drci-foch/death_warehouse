from django.shortcuts import render, redirect
from .models import RecherchePatient
from .forms import RecherchePatientForm
from django.views.generic import ListView

def home(request):
    patients = []
    message = ""

    if request.method == 'POST':
        form = RecherchePatientForm(request.POST)
        if form.is_valid():
            # Le formulaire est valide, traitez-le ici pour effectuer la recherche
            nom = form.cleaned_data.get('nom')
            prenom = form.cleaned_data.get('prenom')
            date_naiss = form.cleaned_data.get('date_naiss')
            # Ajoutez d'autres champs à rechercher en fonction de votre modèle

            # Effectuez la recherche dans la base de données
            patients = RecherchePatient.objects.filter(nom=nom, prenom__icontains=prenom, date_naiss = date_naiss)
            # Vous pouvez ajouter d'autres critères de recherche ici

            if not patients:
                message = "Aucun patient trouvé"
        else:
            message = "Le formulaire n'est pas valide"

    else:
        form = RecherchePatientForm()

    context = {
        'form': form,
        'patients': patients,
        'message': message,
    }

    return render(request, 'death_warehouse_app/home.html', context)


def recherche(request):
    patients = []  # Initialiser une liste vide pour stocker les résultats de la recherche

    if request.method == 'POST':
        form = RecherchePatientForm(request.POST)
        if form.is_valid():
            # Le formulaire est valide, traitez-le ici pour effectuer la recherche
            nom = form.cleaned_data.get('nom')
            prenom = form.cleaned_data.get('prenom')
            date_naiss = form.cleaned_data.get('date_naiss')

            # Effectuez la recherche dans la base de données
            patients = RecherchePatient.objects.filter(nom=nom, prenom__icontains=prenom, date_naiss=date_naiss)

    else:
        form = RecherchePatientForm()

    context = {
        'form': form,
        'patients': patients,
    }

    return render(request, 'death_warehouse_app/home.html', context)

class RecherchePatientListView(ListView):
    model = RecherchePatient
    template_name = 'death_warehouse_app/home.html'  # Utilisez le chemin complet vers le modèle HTML
    context_object_name = 'patients'