from django.views.generic import ListView
from .models import RecherchePatient

from django.shortcuts import render

from .forms import RecherchePatientForm

def home(request):
    if request.method == 'POST':
        form = RecherchePatientForm(request.POST)
        if form.is_valid():
            # Traitez le formulaire ici (par exemple, enregistrez les données)
            form.save()
    else:
        form = RecherchePatientForm()
    
    return render(request, 'death_warehouse_app/home.html', {'form': form})


class RecherchePatientListView(ListView):
    model = RecherchePatient
    template_name = 'recherchepatient_list.html'  # Utilisez le chemin complet vers le modèle HTML
    context_object_name = 'patients'

def traitement_formulaire(request):
    # Redirigez l'utilisateur vers une autre page après le traitement
    return render(request, 'template_de_confirmation.html')

