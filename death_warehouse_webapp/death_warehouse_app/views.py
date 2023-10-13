from django.shortcuts import render
from .models import RecherchePatient
from .forms import RecherchePatientForm, ImportFileForm
from datetime import datetime
import pandas as pd
from django.http import HttpResponse
import csv
import openpyxl

def home(request):
    patients = None
    message = ""

    if request.method == 'POST':
        form = RecherchePatientForm(request.POST)
        if form.is_valid():
            nom = form.cleaned_data.get('nom')
            prenom = form.cleaned_data.get('prenom')
            date_naiss = form.cleaned_data.get('date_naiss')

            # Convert the date to the desired format, i.e., '%Y/%m/%d'
            date_naiss_iso = date_naiss.strftime('%Y/%m/%d') if date_naiss else ""

            patients = RecherchePatient.objects.filter(
                nom__iexact=nom, prenom__icontains=prenom, date_naiss=date_naiss_iso)
        else:
            message = "Le formulaire n'est pas valide"
    else:
        form = RecherchePatientForm()

    # Ajout de la logique de first_load
    first_load = True if not request.POST else False

    context = {
        'form': form,
        'patients': patients,
        'message': message,
        'first_load': first_load,  # Ajout de first_load dans le contexte
    }

    return render(request, 'death_warehouse_app/home.html', context)

def try_parse_date(date_str, formats):
    for date_format in formats:
        try:
            return datetime.strptime(date_str, date_format).strftime('%Y/%m/%d')
        except ValueError:
            continue
    return None


def import_data_from_file(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file, engine='openpyxl')
    else:
        raise ValueError("Unsupported file format")
    return df



def get_verification_results(df):
    date_formats = ['%Y/%m/%d', '%d/%m/%Y', '%Y-%m-%d']
    verification_results = []

    for index, row in df.iterrows():
        date_naiss = row['Date de naissance']

        # Check if date_naiss is missing or not a string or datetime object
        if not date_naiss or not isinstance(date_naiss, (str, pd.Timestamp, datetime)):
            date_naiss_iso = None
        else:
            # If date_naiss is a datetime object or pandas Timestamp, convert it to a string
            if isinstance(date_naiss, (pd.Timestamp, datetime)):
                date_naiss = date_naiss.strftime('%Y/%m/%d')

            # Try to parse the date_naiss string in various formats
            date_naiss_iso = try_parse_date(date_naiss, date_formats)

        patient = RecherchePatient.objects.filter(
            nom__iexact=row['Nom'], prenom__icontains=row['Prenom'], date_naiss=date_naiss_iso).first()

        if patient is not None:
            verification_result = {
                'patient_exists': "Trouvé",
                'patient_details': {
                    'nom': patient.nom,
                    'prenom': patient.prenom,
                    'date_naiss': date_naiss_iso if date_naiss_iso else "Invalid/Empty Date",
                    'date_deces': patient.date_deces.strftime('%Y/%m/%d') if patient.date_deces else ""
                }
            }
        else:
            verification_result = {
                'patient_exists': "Non trouvé",
                'patient_details': {
                    'nom': row['Nom'],
                    'prenom': row['Prenom'],
                    'date_naiss': date_naiss_iso if date_naiss_iso else "Invalid/Empty Date",
                    'date_deces': ""
                }
            }

        verification_results.append(verification_result)

    return verification_results


def import_file(request):
    if request.method == 'POST':
        form = ImportFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            try:
                df = import_data_from_file(file)
                verification_results = get_verification_results(df)
                request.session['verification_results'] = verification_results
                return render(request, 'death_warehouse_app/verification_results.html', {'results': verification_results})
            except ValueError:
                return render(request, 'death_warehouse_app/import_error.html')

    else:
        form = ImportFileForm()

    return render(request, 'death_warehouse_app/import_file.html', {'form': form})


def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y/%m/%d')
        return date_obj.strftime('%d/%m/%Y')
    except ValueError:
        return date_str
def export_results_csv(request):
    verification_results = request.session.get('verification_results')

    if verification_results is not None:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recherche_fichiers_deces.csv"'

        writer = csv.writer(response)
        writer.writerow(['patient_exists', 'nom', 'prenom', 'date_naiss', 'date_deces'])
        
        for result in verification_results:
            formatted_date_naiss = format_date(result['patient_details']['date_naiss'])
            formatted_date_deces = format_date(result['patient_details']['date_deces'])
            
            writer.writerow([
                result['patient_exists'],
                result['patient_details']['nom'],
                result['patient_details']['prenom'],
                formatted_date_naiss,
                formatted_date_deces
            ])

        return response
    else:
        return HttpResponse("Aucun résultat de vérification à exporter.")


def export_results_xlsx(request):
    verification_results = request.session.get('verification_results')

    if verification_results is not None:
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="recherche_fichiers_deces.xlsx"'

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.append(['patient_exists', 'nom', 'prenom', 'date_naiss', 'date_deces'])

        for result in verification_results:
            formatted_date_naiss = format_date(result['patient_details']['date_naiss'])
            formatted_date_deces = format_date(result['patient_details']['date_deces'])
            
            worksheet.append([
                result['patient_exists'],
                result['patient_details']['nom'],
                result['patient_details']['prenom'],
                formatted_date_naiss,
                formatted_date_deces
            ])

        workbook.save(response)
        return response
    else:
        return HttpResponse("Aucun résultat de vérification à exporter.")
