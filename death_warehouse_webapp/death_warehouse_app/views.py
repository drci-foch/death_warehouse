from audioop import reverse
import os
import re
from unittest import loader
from django.shortcuts import redirect
import subprocess
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
from django.shortcuts import render
from django.db import connections
import cx_Oracle

# --------------------------------------------------------------------------------- Search home part 

import subprocess
import sys
from django.http import HttpResponse


def get_recent_death_date():
    directory = './deces_insee'
    latest_date = None

    for filename in os.listdir(directory):
        if filename.startswith("deces_global_maj_"):
            try:
                date_str = filename.split('_')[-1]
                date_obj = datetime.strptime(date_str, '%d%m%Y')
                if latest_date is None or date_obj > latest_date:
                    latest_date = date_obj
            except ValueError:
                continue

    return latest_date # Remplacez 'your_template.html' par le nom de votre template
def latestdate(request):
    recent_death_date = get_recent_death_date()
    print(recent_death_date)
    context = {
        'recent_death_date': recent_death_date.strftime('%d/%m/%Y') if recent_death_date else 'Aucune date trouvée',
    }
    print(context)
    
    return render(request, 'import_file.html', context)  # Remplacez 'your_template.html' par le nom de votre template

def run_scripts(request):
    if request.method == 'POST':
        try:
            # Chemin vers l'interpréteur Python de Django
            python_executable = sys.executable
            
            # Chemins absolus complets des scripts à exécuter
            script1 = '../00_ApiRequest.py'
            script2 = '../01_ParserINSEE.py'
            script3 = '../death_warehouse_webapp/initial_import_data.py'

            # Exécuter les scripts nécessaires
            result1 = subprocess.run([python_executable, script1], capture_output=True, text=True)
            result2 = subprocess.run([python_executable, script2], capture_output=True, text=True)
            result3 = subprocess.run([python_executable, script3], capture_output=True, text=True)

            # Afficher la sortie du script pour le débogage
            print(result1.stdout)
            print(result1.stderr)

            print(result2.stdout)
            print(result2.stderr)

            print(result3.stdout)
            print(result3.stderr)
            # Vérifier le code de retour
            return HttpResponse('Scripts exécutés avec succès.')

        except Exception as e:
            return  HttpResponse(f'Une erreur s\'est produite : {str(e)}', status=500)

    return  HttpResponse('Method not allowed', status=405)



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
                'mail': patient.MAIL,
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


# --------------------------------------------------------------------------------- Import  


def import_data_from_file(file):
    if file.name.endswith('.csv'):
        try:
            df = pd.read_csv(file)

            return df
        except Exception as e:

            raise ValueError("Erreur lors de la lecture du fichier CSV")
    elif file.name.endswith(('.xls', '.xlsx')):
        try:
            df = pd.read_excel(file, engine='openpyxl')
            return df
        except Exception as e:

            raise ValueError("Erreur lors de la lecture du fichier Excel")
    else:
        raise ValueError("Format de fichier non pris en charge")


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
    page_size = 100 
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
                'mail': patient.MAIL,
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

def search_patient(nom_naiss, nom_usage, prenom, date_naiss_iso):
    # Try to find the patient in WarehousePatient first
    warehouse_patient = WarehousePatient.objects.filter(
        Q(LASTNAME__iexact=nom_usage) & Q(BIRTH_DATE=date_naiss_iso) & Q(FIRSTNAME__icontains=prenom)
    ).first()

    if warehouse_patient:
        return warehouse_patient

    # If not found, try INSEEPatient using usage name
    inseepatient = INSEEPatient.objects.filter(
        Q(nom__iexact=nom_usage) & Q(prenom__icontains=prenom) & Q(date_naiss=date_naiss_iso)
    ).first()

    # If still not found and birth name differs from usage name, try INSEEPatient with birth name
    if not inseepatient and nom_naiss != nom_usage:
        inseepatient = INSEEPatient.objects.filter(
            Q(nom__iexact=nom_naiss) & Q(prenom__icontains=prenom) & Q(date_naiss=date_naiss_iso)
        ).first()

    return inseepatient


# Main function with batch processing

def get_verification_results(df):
    date_formats = ['%d/%m/%Y', '%Y-%m-%d']
    verification_results = []
    batch_size = 300

    for start in range(0, len(df), batch_size):
        end = start + batch_size
        batch_df = df[start:end]

        for index, row in batch_df.iterrows():
            date_naiss_iso = parse_date(row['Date de naissance'], date_formats)
            ipp = row['IPP']
            nom_usage = row['Nom']
            nom_naiss = row.get('Nom de naissance', '')
            prenom = row.get('Prénom', '')

            patient = search_patient(nom_naiss, nom_usage, prenom, date_naiss_iso)

            if patient:
                verification_result = create_verification_result(patient, date_naiss_iso, True, ipp=ipp)
            else:
                verification_result = create_verification_result(row, date_naiss_iso, False, ipp=ipp)

            verification_results.append(verification_result)

    return verification_results

# --------------------------------------------------------------------------------- Display results 
# views.py
import os
import json
from django.http import JsonResponse

def get_recent_death_date_from_database(request):
    try:
        # Récupérer la date la plus récente depuis la base de données
        most_recent_date = INSEEPatient.objects.latest('date_deces').date_deces.strftime('%d/%m/%Y')
        return JsonResponse({'recent_death_date': most_recent_date})
    except INSEEPatient.DoesNotExist:
        return JsonResponse({'error': 'Aucune donnée trouvée dans la base de données.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
def get_files_in_folder(request):
    try:
        # Récupérer la date la plus récente depuis la base de données
        most_recent_date = INSEEPatient.objects.latest('date_deces').date_deces.strftime('%d/%m/%Y')
        return JsonResponse({'recent_death_date': most_recent_date})
    except INSEEPatient.DoesNotExist:
        return JsonResponse({'error': 'Aucune donnée trouvée dans la base de données.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    folder_path = './deces_insee'  # Mettez le chemin absolu de votre dossier deces_insee ici
    # Fonction pour extraire la date du nom de fichier
    def extract_date_from_filename(filename):
        # Regex pour extraire la date (ici, le motif suppose une date au format DDMMYYYY)
        match = re.search(r'_([0-9]{2})([0-9]{2})([0-9]{4})', filename)
        if match:
            day = match.group(1)
            month = match.group(2)
            year = match.group(3)
            return f"{day}/{month}/{year}"
        return None

    # Récupérer la liste des fichiers dans le dossier
    if os.path.isdir(folder_path):
        files = os.listdir(folder_path)
        files_in_folder = [f for f in files if os.path.isfile(os.path.join(folder_path, f))]

        # Filtrer le fichier commençant par deces_global_maj_
        filtered_files = [f for f in files_in_folder if f.startswith('deces_global_maj_')]

        # Extraire la date du premier fichier trouvé
        if filtered_files:
            first_file = filtered_files[0]
            date_from_filename = extract_date_from_filename(first_file)
        else:
            date_from_filename = None

        # Renvoyer la date au format JSON
        return JsonResponse({'recent_death_date': date_from_filename})
    else:
        return JsonResponse({'error': 'Le dossier deces_insee n\'existe pas ou n\'est pas accessible.'}, status=400)

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
            except KeyError as e:
                return render(request, 'friendly_error_page.html', {'error_message': str(e)})


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
            return "Invalid Format"
    return "" 



def execute_sql_query(sql_query, database='my_oracle'):
    """
    Execute an SQL query and return the results as a list of dictionaries.
    The 'database' parameter is optional and defaults to 'my_oracle'.
    This function expects connections to be available globally under the name 'connections'.
    """
    connection = connections[database]  
    
    cursor = connection.cursor()
    result = []
    try:
        cursor.execute(sql_query)
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        for row in rows:
            item = {}
            for i, col in enumerate(row):
                if col is not None:
                    item[columns[i]] = str(col)
            result.append(item)
        
    except Exception as e:
        print("Error executing SQL query:", e)
    
    finally:
        cursor.close()
    
    return result


def get_emails_for_ipps(verification_results):
    # Extract IPPs
    ipps = [result['patient_details']['ipp'] for result in verification_results]

    # Split IPPs into batches of 500
    batch_size = 500
    ipps_batches = [ipps[i:i + batch_size] for i in range(0, len(ipps), batch_size)]

    # Placeholder for database query execution
    email_data = []

    for batch in ipps_batches:
        # Create a comma-separated string of IPPs for the SQL query
        ipp_list = ','.join([f"'{ipp}'" for ipp in batch])

        sql_query = f"""
        SELECT 
            ipph.HOSPITAL_PATIENT_ID AS "IPP",
            p.EMAIL AS "Mail",
            p.RESIDENCE_ADDRESS as "Adresse",
            p.ZIP_CODE as "ZIP",
            p.RESIDENCE_CITY as "Ville",
            p.RESIDENCE_COUNTRY as "Pays"
        FROM 
            DWH.DWH_PATIENT p
        LEFT JOIN 
            DWH.DWH_PATIENT_IPPHIST ipph ON p.PATIENT_NUM = ipph.PATIENT_NUM
        WHERE 
            ipph.HOSPITAL_PATIENT_ID IN ({ipp_list})
        """
        print(sql_query)
        # Execute the query for the batch and append the results
        batch_results = execute_sql_query(sql_query)  # This function should return a dictionary {IPP: email}
        email_data.extend(batch_results)

    return email_data

# --------------------------------------------------------------------------------- Exporting results

def export_results_csv(request):
    verification_results = request.session.get('verification_results')
    email_data = get_emails_for_ipps(verification_results)  # Get email data

    if verification_results is not None:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="recherche_fichiers_deces.csv"'
        response.write(u'\ufeff'.encode('utf8'))  # BOM (optional; for Excel compatibility)

        writer = csv.writer(response)
        writer.writerow(['Source', 'IPP', 'Nom', 'Prénom', 'Date de naissance', 'Date de décès', 'Mail','Adresse','Code','Ville','Pays'])
    
        for result in verification_results:
            formatted_date_naiss = format_date(result['patient_details']['date_naiss'])
            formatted_date_deces = format_date(result['patient_details']['date_deces'])
            
            ipp = str(result['patient_details']['ipp']) 

            # Find the email associated with the IPP
            email = next((item.get('Mail', '') for item in email_data if item.get('IPP') == ipp), '')
            adress = next((item.get('Adresse', '') for item in email_data if item.get('IPP') == ipp), '')
            code = next((item.get('ZIP', '') for item in email_data if item.get('IPP') == ipp), '')
            ville = next((item.get('Ville', '') for item in email_data if item.get('IPP') == ipp), '')
            pays = next((item.get('Pays', '') for item in email_data if item.get('IPP') == ipp), '')


            writer.writerow([
                result['patient_exists'],
                ipp,
                result['patient_details']['nom'],
                result['patient_details']['prenom'],
                formatted_date_naiss,
                formatted_date_deces,
                email,
                adress,
                code,
                ville,
                pays
            ])

        return response
    else:
        print("No verification results found in the session.")  # Debug statement
        return HttpResponse("Aucun résultat de vérification à exporter.")

def export_results_xlsx(request):
    verification_results = request.session.get('verification_results')
    #email_data = get_emails_for_ipps(verification_results)  # Get email data

    if verification_results is not None:
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="recherche_fichiers_deces.xlsx"'

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.append(['Source', 'IPP', 'Nom', 'Prénom', 'Date de naissance', 'Date de décès', 'Mail', 'Adresse','Code','Ville','Pays'])

        for result in verification_results:
            formatted_date_naiss = format_date(result['patient_details']['date_naiss'])
            formatted_date_deces = format_date(result['patient_details']['date_deces'])
            ipp = str(result['patient_details']['ipp'])
            
            # Find the email associated with the IPP
            #email = next((item.get('Mail', '') for item in email_data if item.get('IPP') == ipp), '')
            #adress = next((item.get('Adresse', '') for item in email_data if item.get('IPP') == ipp), '')
            #code = next((item.get('ZIP', '') for item in email_data if item.get('IPP') == ipp), '')
            #ville = next((item.get('Ville', '') for item in email_data if item.get('IPP') == ipp), '')
            #pays = next((item.get('Pays', '') for item in email_data if item.get('IPP') == ipp), '')

            worksheet.append([
                result['patient_exists'],
                ipp,
                result['patient_details']['nom'],
                result['patient_details']['prenom'],
                formatted_date_naiss,
                formatted_date_deces,
                #email,
                #adress,
                #code,
                #ville,
                #pays
            ])

        workbook.save(response)
        return response
    else:
        return HttpResponse("Aucun résultat de vérification à exporter.")
