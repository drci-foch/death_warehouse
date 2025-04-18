import csv
from datetime import datetime

import openpyxl
import pandas as pd
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db import connections
from django.db.models import Count, Max, Q
from django.db.models.functions import TruncDay, TruncMonth
from django.http import HttpResponse
from django.shortcuts import render

from .forms import ImportFileForm, INSEEPatientForm
from .log_utils import log_user_action
from .models import INSEEPatient, UserActionLog, WarehousePatient
from .utils import fetch_merged_data

# --------------------------------------------------------------------------------- Search home part


def format_date_for_display(date):
    if date:
        return date.strftime("%d/%m/%Y")
    return ""


def get_patients_data(nom, prenom, date_naiss_iso):
    """
    Retrieve patients data from INSEEPatient and WarehousePatient models based on given parameters.
    """

    inseepatients = INSEEPatient.objects.filter(nom__iexact=nom, prenom__icontains=prenom, date_naiss=date_naiss_iso)
    warehousepatients = WarehousePatient.objects.filter(
        LASTNAME__iexact=nom, FIRSTNAME__icontains=prenom, BIRTH_DATE=date_naiss_iso
    )

    return list(inseepatients) + list(warehousepatients)


def format_patient_data(patients):
    """
    Format patients data for display.
    """
    formatted_patients = []
    for patient in patients:
        if isinstance(patient, INSEEPatient):
            formatted_patient = {
                "nom": patient.nom,
                "prenom": patient.prenom,
                "date_naiss": format_date_for_display(patient.date_naiss),
                "date_deces": format_date_for_display(patient.date_deces),
                "source": "INSEE",
            }

        elif isinstance(patient, WarehousePatient):
            formatted_patient = {
                "nom": patient.LASTNAME,
                "prenom": patient.FIRSTNAME,
                "mail": patient.MAIL,
                "date_naiss": format_date_for_display(patient.BIRTH_DATE),
                "date_deces": format_date_for_display(patient.DEATH_DATE),
                "source": "Warehouse",
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

    nom = form.cleaned_data.get("nom")
    prenom = form.cleaned_data.get("prenom")
    date_naiss = form.cleaned_data.get("date_naiss")
    date_naiss_iso = date_naiss.strftime("%Y-%m-%d") if date_naiss else None

    patients = get_patients_data(nom, prenom, date_naiss_iso)
    formatted_patients = format_patient_data(patients)

    return formatted_patients, "", form


def home(request):
    # Utiliser le cache pour la date de décès la plus récente
    latest_death_date = cache.get("latest_death_date")
    if latest_death_date is None:
        # Si pas en cache, obtenir la valeur et la mettre en cache
        latest_death_date = INSEEPatient.objects.aggregate(Max("date_deces"))["date_deces__max"]
        # Cache pour 1 semaine (604800 secondes)
        cache.set("latest_death_date", latest_death_date, 604800)

    if request.method == "POST":
        patients, message, form = handle_post_request(request)
        # Log the search action
        if form.is_valid():
            log_details = {
                "nom": form.cleaned_data.get("nom", ""),
                "prenom": form.cleaned_data.get("prenom", ""),
                "date_naiss": str(form.cleaned_data.get("date_naiss", "")),
                "results_count": len(patients) if patients else 0,
            }
            log_user_action(request, "search", log_details)
    else:
        form = INSEEPatientForm()
        patients, message = None, ""

    first_load = not request.POST
    context = {
        "form": form,
        "patients": patients,
        "message": message,
        "first_load": first_load,
        "latest_death_date": latest_death_date,
    }
    return render(request, "death_warehouse_app/home.html", context)


# --------------------------------------------------------------------------------- Import
def import_data_from_file(file) -> pd.DataFrame:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    elif file.name.endswith((".xls", ".xlsx")):
        df = pd.read_excel(file, engine="openpyxl")
    else:
        raise ValueError("Format de fichier non pris en charge")
    return df


def try_parse_date(date_str, formats):
    # Split the string and keep only the date part
    date_part = date_str.split(" ")[0]

    for date_format in formats:
        try:
            # Parse the date and format it in the Django expected format (YYYY-MM-DD)
            return datetime.strptime(date_part, date_format).date().isoformat()
        except ValueError:
            continue
    return None


def parse_date(date_value, date_formats):
    if not date_value or not isinstance(date_value, str | pd.Timestamp | datetime):
        return None
    if isinstance(date_value, pd.Timestamp | datetime):
        date_value = date_value.strftime("%Y-%m-%d")
    return try_parse_date(date_value, date_formats)


def patient_data_view(request):
    page = request.GET.get("page", 1)
    page_size = 100
    data = fetch_merged_data(page=page, page_size=page_size)

    return render(request, "test.html", {"data": data, "page": page})


# --------------------------------------------------------------------------------- Searching part
# Improved database query
def search_inseepatient(nom, prenom, date_naiss_iso):
    return INSEEPatient.objects.filter(
        Q(nom__iexact=nom) & (Q(prenom__icontains=prenom) & Q(date_naiss=date_naiss_iso))
    ).first()


def create_verification_result(patient, date_naiss_iso, found, ipp=None, source=None):
    if found:
        if isinstance(patient, INSEEPatient):
            patient_details = {
                "ipp": ipp,
                "nom": patient.nom,
                "prenom": patient.prenom,
                "date_naiss": patient.date_naiss.strftime("%Y-%m-%d"),
                "date_deces": patient.date_deces.strftime("%Y-%m-%d") if patient.date_deces else "",
            }
            source = "INSEE"
    else:
        patient_details = {
            "ipp": ipp,
            "nom": patient["Nom"],
            "prenom": patient["Prénom"],
            "date_naiss": date_naiss_iso if date_naiss_iso else "Date invalide/vide",
            "date_deces": "",
        }

    return {
        "patient_exists": f"{source}" if found else "Non trouvé",
        "patient_details": patient_details,
    }


def search_patient(nom_naiss, nom_usage, prenom, date_naiss_iso) -> INSEEPatient | None:
    inseepatient = INSEEPatient.objects.filter(
        Q(nom__iexact=nom_usage) & Q(prenom__icontains=prenom) & Q(date_naiss=date_naiss_iso)
    ).first()

    if not inseepatient and nom_naiss != nom_usage:
        inseepatient = INSEEPatient.objects.filter(
            Q(nom__iexact=nom_naiss) & Q(prenom__icontains=prenom) & Q(date_naiss=date_naiss_iso)
        ).first()

    return inseepatient


def get_verification_results(df: pd.DataFrame) -> list:
    date_formats = ["%d/%m/%Y", "%Y-%m-%d"]
    verification_results = []
    batch_size = 300

    for start in range(0, len(df), batch_size):
        end = start + batch_size
        batch_df = df[start:end]

        for _, row in batch_df.iterrows():
            date_naiss_iso = parse_date(row["Date de naissance"], date_formats)
            ipp = row["IPP"]
            nom_usage = row["Nom"]
            nom_naiss = row.get("Nom de naissance", "")
            prenom = row.get("Prénom", "")

            patient = search_patient(nom_naiss, nom_usage, prenom, date_naiss_iso)

            if patient:
                verification_result = create_verification_result(patient, date_naiss_iso, True, ipp=ipp)
            else:
                verification_result = create_verification_result(row, date_naiss_iso, False, ipp=ipp)

            verification_results.append(verification_result)

    return verification_results


# --------------------------------------------------------------------------------- Display results
def import_file(request):
    if request.method == "POST":
        form = ImportFileForm(request.POST, request.FILES)

        if form.is_valid():
            file = form.cleaned_data["file"]
            try:
                # Log the file import action
                log_details = {
                    "filename": file.name,
                    "filesize": file.size,
                    "file_type": file.content_type,
                }
                log_user_action(request, "import_file", log_details)

                df = import_data_from_file(file)

                verification_results = get_verification_results(df)

                request.session["verification_results"] = verification_results
                return render(
                    request,
                    "death_warehouse_app/verification_results.html",
                    {"results": verification_results},
                )
            except ValueError:
                return render(request, "death_warehouse_app/import_error.html")
            except KeyError as e:
                return render(request, "friendly_error_page.html", {"error_message": str(e)})
    else:
        form = ImportFileForm()

    return render(request, "death_warehouse_app/import_file.html", {"form": form})


def format_date(date_str):
    if date_str:
        try:
            # Assuming date_str is in 'yyyy-mm-dd' format
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d/%m/%Y")
        except ValueError:
            return "Invalid Format"
    return ""


def execute_sql_query(sql_query, database="my_oracle"):
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
    ipps = [result["patient_details"]["ipp"] for result in verification_results]

    # Split IPPs into batches of 500
    batch_size = 500
    ipps_batches = [ipps[i : i + batch_size] for i in range(0, len(ipps), batch_size)]

    # Placeholder for database query execution
    email_data = []

    for batch in ipps_batches:
        # Create a comma-separated string of IPPs for the SQL query
        ipp_list = ",".join([f"'{ipp}'" for ipp in batch])

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
    verification_results = request.session.get("verification_results")

    if verification_results is not None:
        # Log the CSV export action
        log_details = {"records_count": len(verification_results), "format": "CSV"}
        log_user_action(request, "export_csv", log_details)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="recherche_fichiers_deces.csv"'
        response.write("\ufeff".encode())  # BOM (optional; for Excel compatibility)

        writer = csv.writer(response)
        writer.writerow(
            [
                "Source",
                "IPP",
                "Nom",
                "Prénom",
                "Date de naissance",
                "Date de décès",
                "Mail",
                "Adresse",
                "Code",
                "Ville",
                "Pays",
            ]
        )

        for result in verification_results:
            formatted_date_naiss = format_date(result["patient_details"]["date_naiss"])
            formatted_date_deces = format_date(result["patient_details"]["date_deces"])

            ipp = str(result["patient_details"]["ipp"])

            writer.writerow(
                [
                    result["patient_exists"],
                    ipp,
                    result["patient_details"]["nom"],
                    result["patient_details"]["prenom"],
                    formatted_date_naiss,
                    formatted_date_deces,
                ]
            )

        return response
    else:
        print("No verification results found in the session.")  # Debug statement
        return HttpResponse("Aucun résultat de vérification à exporter.")


def export_results_xlsx(request):
    verification_results = request.session.get("verification_results")

    if verification_results is not None:
        # Log the Excel export action
        log_details = {"records_count": len(verification_results), "format": "XLSX"}
        log_user_action(request, "export_xlsx", log_details)

        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = 'attachment; filename="recherche_fichiers_deces.xlsx"'

        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.append(
            [
                "Source",
                "IPP",
                "Nom",
                "Prénom",
                "Date de naissance",
                "Date de décès",
                "Mail",
                "Adresse",
                "Code",
                "Ville",
                "Pays",
            ]
        )

        for result in verification_results:
            formatted_date_naiss = format_date(result["patient_details"]["date_naiss"])
            formatted_date_deces = format_date(result["patient_details"]["date_deces"])
            ipp = str(result["patient_details"]["ipp"])

            worksheet.append(
                [
                    result["patient_exists"],
                    ipp,
                    result["patient_details"]["nom"],
                    result["patient_details"]["prenom"],
                    formatted_date_naiss,
                    formatted_date_deces,
                ]
            )

        workbook.save(response)
        return response
    else:
        return HttpResponse("Aucun résultat de vérification à exporter.")


@staff_member_required
def log_stats(request):
    """View to display statistics about user actions"""

    # Get action counts
    action_counts = UserActionLog.objects.values("action").annotate(count=Count("action")).order_by("-count")

    # Get daily stats for the past 30 days
    from datetime import timedelta

    from django.utils import timezone

    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_stats = (
        UserActionLog.objects.filter(timestamp__gte=thirty_days_ago)
        .annotate(day=TruncDay("timestamp"))
        .values("day", "action")
        .annotate(count=Count("id"))
        .order_by("day", "action")
    )

    # Get monthly stats
    monthly_stats = (
        UserActionLog.objects.annotate(month=TruncMonth("timestamp"))
        .values("month", "action")
        .annotate(count=Count("id"))
        .order_by("month", "action")
    )

    # Recent logs
    recent_logs = UserActionLog.objects.all().order_by("-timestamp")[:50]

    context = {
        "action_counts": action_counts,
        "daily_stats": daily_stats,
        "monthly_stats": monthly_stats,
        "recent_logs": recent_logs,
    }

    return render(request, "death_warehouse_app/log_stats.html", context)
