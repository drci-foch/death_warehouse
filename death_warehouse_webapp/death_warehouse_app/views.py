from django.shortcuts import render
from .models import INSEEPatient, WarehousePatient
from .forms import INSEEPatientForm, ImportFileForm
from datetime import datetime
import pandas as pd
from django.http import HttpResponse
import csv
import openpyxl
from django.db.models import Q
from .utils import fetch_merged_data  
from django.core.cache import cache


# --------------------------------------------------------------------------------- Search home part 

def format_date_for_display(date):
    if date:
        return date.strftime('%d/%m/%Y')
    return ""
def get_patients_data(nom, prenom, date_naiss_iso):
    """
    Retrieve patients data from INSEEPatient and WarehousePatient models based on given parameters.
    """

    inseepatients = INSEEPatient.objects.filter(
        nom__iexact=nom, prenom__icontains=prenom, date_naiss=date_naiss_iso)
    warehousepatients = WarehousePatient.objects.filter(
        LASTNAME__iexact=nom, FIRSTNAME__icontains=prenom, BIRTH_DATE=date_naiss_iso)

    return list(inseepatients) + list(warehousepatients)

def format_patient_data(patients):
    """
    Format patients data for display.
    """
    formatted_patients = []
    for patient in patients:
        if isinstance(patient, INSEEPatient):
            formatted_patient = {
                'nom': patient.nom,
                'prenom': patient.prenom,
                'date_naiss': format_date_for_display(patient.date_naiss),
                'date_deces': format_date_for_display(patient.date_deces),
                'source': 'INSEE'
            }
        
        elif isinstance(patient, WarehousePatient):
            formatted_patient = {
                'nom': patient.LASTNAME,
                'prenom': patient.FIRSTNAME,
                'date_naiss': format_date_for_display(patient.BIRTH_DATE),
                'date_deces': format_date_for_display(patient.DEATH_DATE),
                'source': 'Warehouse'
            }
        formatted_patients.append(formatted_patient)
    return formatted_patients

def handle_post_request(request):
    """
    Handle POST request and return patients data if the form is valid.
    """
    form = INSEEPatientForm(request.POST)
    if not form.is_valid():
        return None, "Le formulaire n'est pas valide", form

    nom = form.cleaned_data.get('nom')
    prenom = form.cleaned_data.get('prenom')
    date_naiss = form.cleaned_data.get('date_naiss')
    date_naiss_iso = date_naiss.strftime('%Y-%m-%d') if date_naiss else None

    patients = get_patients_data(nom, prenom, date_naiss_iso)
    formatted_patients = format_patient_data(patients)

    return formatted_patients, "", form

def home(request):
    if request.method == 'POST':
        patients, message, form = handle_post_request(request)
    else:
        form = INSEEPatientForm()
        patients, message = None, ""

    first_load = not request.POST
    context = {'form': form, 'patients': patients, 'message': message, 'first_load': first_load}
    return render(request, 'death_warehouse_app/home.html', context)


# --------------------------------------------------------------------------------- Import part 

def import_data_from_file(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(file, engine='openpyxl')
    else:
        raise ValueError("Unsupported file format")

    return df


def try_parse_date(date_str, formats):
    # Split the string and keep only the date part
    date_part = date_str.split(' ')[0]

    for date_format in formats:
        try:
            # Parse the date and format it in the Django expected format (YYYY-MM-DD)

            return datetime.strptime(date_part, date_format).date().isoformat()
        except ValueError:
            continue
    return None

def parse_date(date_value, date_formats):
    if not date_value or not isinstance(date_value, (str, pd.Timestamp, datetime)):
        return None
    if isinstance(date_value, (pd.Timestamp, datetime)):
        date_value = date_value.strftime('%Y-%m-%d')
    return try_parse_date(date_value, date_formats)

def patient_data_view(request):
    page = request.GET.get('page', 1)
    page_size = 100  # Or any number you prefer
    data = fetch_merged_data(page=page, page_size=page_size)

    return render(request, 'test.html', {'data': data, 'page': page})

# --------------------------------------------------------------------------------- Searching part 

# Improved database query
def search_inseepatient(nom, prenom, date_naiss_iso):
    return INSEEPatient.objects.filter(
        Q(nom__iexact=nom) & (Q(prenom__icontains=prenom) & Q(date_naiss=date_naiss_iso))
    ).first()

def search_warehousepatient(nom, prenom, date_naiss_iso):
    warehouse_patients_query = Q(LASTNAME__iexact=nom) & Q(BIRTH_DATE=date_naiss_iso) & Q(FIRSTNAME__icontains=prenom)
    return WarehousePatient.objects.filter(warehouse_patients_query).first()

def create_verification_result(patient, date_naiss_iso, found, ipp=None, source=None):


    if found:
        if isinstance(patient, INSEEPatient):
            patient_details = {
                'ipp': ipp,
                'nom': patient.nom,
                'prenom': patient.prenom,
                'date_naiss': patient.date_naiss.strftime('%Y-%m-%d'),
                'date_deces': patient.date_deces.strftime('%Y-%m-%d') if patient.date_deces else ""
            }
            source = 'INSEE'
        elif isinstance(patient, WarehousePatient):
            patient_details = {
                'ipp': ipp,
                'nom': patient.LASTNAME,
                'prenom': patient.FIRSTNAME,
                'date_naiss': patient.BIRTH_DATE.strftime('%Y-%m-%d'),  
                'date_deces': patient.DEATH_DATE.strftime('%Y-%m-%d') if patient.DEATH_DATE else ""
            }
            source = 'Warehouse'
    else:
        patient_details = {
            'ipp': ipp,
            'nom': patient['Nom'],
            'prenom': patient['Prénom'],
            'date_naiss': date_naiss_iso if date_naiss_iso else "Date invalide/vide",  
            'date_deces': ""
        }

    return {
        'patient_exists': f"{source}" if found else "Non trouvé",
        'patient_details': patient_details
    }

# Function with caching
def search_patient(nom, prenom, date_naiss_iso):
    # First try to find the patient in the WarehousePatient model
    patient = search_warehousepatient(nom, prenom, date_naiss_iso)

    # If not found in WarehousePatient, then try in INSEEPatient
    if not patient:
        patient = search_inseepatient(nom, prenom, date_naiss_iso)

    return patient


# Main function with batch processing
def get_verification_results(df):
    date_formats = ['%d/%m/%Y', '%Y-%m-%d'] 
    verification_results = []
    batch_size = 500  

    for start in range(0, len(df), batch_size):
        end = start + batch_size
        batch_df = df[start:end]

        for index, row in batch_df.iterrows():
            date_naiss_iso = parse_date(row['Date de naissance'], date_formats)
       
            ipp = row['IPP']
            nom = row['Nom']
            prenom = row.get('Prénom', '')
  
            patient = search_patient(nom, prenom, date_naiss_iso)
            if patient:
                verification_result = create_verification_result(patient, date_naiss_iso, True, ipp=ipp)
            else:
                verification_result = create_verification_result(row, date_naiss_iso, False, ipp=ipp)

            verification_results.append(verification_result)

    return verification_results

# --------------------------------------------------------------------------------- Display results part

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
    if date_str:
        try:
            # Assuming date_str is in 'yyyy-mm-dd' format
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d/%m/%Y')
        except ValueError:
            return "Invalid Format"  # or return original date_str or empty string
    return "" 

def export_results_csv(request):
    verification_results = request.session.get('verification_results')

    if verification_results is not None:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recherche_fichiers_deces.csv"'
        response.write(u'\ufeff'.encode('utf8'))  # BOM (optional; for Excel compatibility)

        writer = csv.writer(response)
        writer.writerow(['Source', 'IPP', 'Nom', 'Prénom', 'Date de naissance', 'Date de décès'])

        for result in verification_results:
            formatted_date_naiss = format_date(result['patient_details']['date_naiss'])
            formatted_date_deces = format_date(result['patient_details']['date_deces'])

            writer.writerow([
                result['patient_exists'],
                result['patient_details']['ipp'],
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
        worksheet.append(['Source', 'IPP', 'Nom', 'Prénom', 'Date de naissance', 'Date de décès'])

        for result in verification_results:
            formatted_date_naiss = format_date(result['patient_details']['date_naiss'])
            formatted_date_deces = format_date(result['patient_details']['date_deces'])

            worksheet.append([
                result['patient_exists'],
                result['patient_details']['ipp'],
                result['patient_details']['nom'],
                result['patient_details']['prenom'],
                formatted_date_naiss,
                formatted_date_deces
            ])


        workbook.save(response)
        return response
    else:
        return HttpResponse("Aucun résultat de vérification à exporter.")
