from django.views.generic import ListView
from .models import RecherchePatient

from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

class RecherchePatientListView(ListView):
    model = RecherchePatient
    template_name = 'recherchepatient_list.html'  # Utilisez le chemin complet vers le modèle HTML
    context_object_name = 'patients'
