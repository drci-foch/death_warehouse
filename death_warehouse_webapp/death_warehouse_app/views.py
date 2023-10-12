from django.shortcuts import render
from .models import RecherchePatient
from .forms import RecherchePatientForm, ImportFileForm
from django.views.generic import ListView
from datetime import datetime
import pandas as pd
from django.http import HttpResponse
import csv

def home(request):
    patients = None
    message = ""

    if request.method == 'POST':
        form = RecherchePatientForm(request.POST)
        if form.is_valid():
            nom = form.cleaned_data.get('nom')
            prenom = form.cleaned_data.get('prenom')
            date_naiss = form.cleaned_data.get('date_naiss')
            patients = RecherchePatient.objects.filter(nom__iexact=nom, prenom__icontains=prenom, date_naiss=date_naiss)
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

def import_file(request):
    if request.method == 'POST':
        form = ImportFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']

            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                return render(request, 'death_warehouse_app/import_error.html')

            verification_results = []

            for index, row in df.iterrows():
                date_naiss = row['Date de naissance']

                try:
                    # Essayer de convertir la date au format 'dd-mm-yyyy'
                    date_naiss_iso = datetime.strptime(date_naiss, '%d-%m-%Y').strftime('%Y-%m-%d')
                except ValueError:
                    # En cas d'erreur de format, définissez la date à une valeur par défaut ou à None
                    date_naiss_iso = None  # ou une autre valeur par défaut si nécessaire

                patient = RecherchePatient.objects.filter(nom__iexact=row['Nom'], prenom__icontains=row['Prenom'], date_naiss=date_naiss_iso).first()

                if patient is not None:
                    verification_result = {
                        'patient_exists': "Trouvé",
                        'patient_details': {
                            'nom': patient.nom,
                            'prenom': patient.prenom,
                            'date_naiss': patient.date_naiss.isoformat(),
                            'date_deces': patient.date_deces.isoformat() if patient.date_deces else ""
                        }
                    }
                else:
                    verification_result = {
                        'patient_exists': "Non trouvé",
                        'patient_details': {
                            'nom': row['Nom'],
                            'prenom': row['Prenom'],
                            'date_naiss': date_naiss_iso if date_naiss_iso else "",
                            'date_deces': ""
                        }
                    }

                verification_results.append(verification_result)


            request.session['verification_results'] = verification_results

            return render(request, 'death_warehouse_app/verification_results.html', {'results': verification_results})
    else:
        form = ImportFileForm()

    return render(request, 'death_warehouse_app/import_file.html', {'form': form})

import csv
from django.http import HttpResponse

def export_results_csv(request):
    verification_results = request.session.get('verification_results')

    if verification_results is not None:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="verification_results.csv"'

        writer = csv.writer(response)
        writer.writerow(['patient_exists', 'nom', 'prenom', 'date_naiss', 'date_deces'])
        for result in verification_results:
            writer.writerow([
                result['patient_exists'],
                result['patient_details']['nom'],
                result['patient_details']['prenom'],
                result['patient_details']['date_naiss'],
                result['patient_details']['date_deces']
            ])

        return response
    else:
        return HttpResponse("Aucun résultat de vérification à exporter.")
