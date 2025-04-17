import csv
import os
from datetime import datetime
from pathlib import Path

import django
from death_warehouse_app.models import INSEEPatient
from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "death_warehouse_webapp.settings")
django.setup()


def import_data_from_csv(file_path):
    # Clear existing data
    INSEEPatient.objects.all().delete()

    patients_to_create = []

    with open(
        file_path, encoding="latin-1", errors="ignore"
    ) as csvfile:  # Try 'latin-1', 'ISO-8859-1', or 'Windows-1252'
        reader = csv.DictReader(csvfile)

        for row in reader:
            nom = row.get("Nom", "Nom manquant")
            prenom = row.get("Prenom", "Prénom Manquant")
            date_naiss = row.get("Date de naissance", None)
            pays_naiss = row.get("Pays de naissance", "Pays de naissance manquant")
            lieu_naiss = row.get("Lieu de naissance", "Lieu de naissance manquant")
            code_naiss = row.get("Code lieu de naissance", "00000")
            date_deces = row.get("Date de deces", None)

            # Convert date_naiss and date_deces to date objects (YYYY/MM/DD format)
            if date_naiss:
                try:
                    date_naiss = datetime.strptime(date_naiss, "%Y/%m/%d").date()
                except ValueError:
                    date_naiss = None
                    print(f"Invalid date format for date of birth: {row.get('Date de naissance')}")

            if date_deces:
                try:
                    date_deces = datetime.strptime(date_deces, "%Y/%m/%d").date()
                except ValueError:
                    date_deces = None
                    print(f"Invalid date format for death date: {row.get('Date de deces')}")

            # Create INSEEPatient instance (not saved to database yet)
            patients_to_create.append(
                INSEEPatient(
                    nom=nom,
                    prenom=prenom,
                    date_naiss=date_naiss,
                    pays_naiss=pays_naiss,
                    lieu_naiss=lieu_naiss,
                    code_naiss=code_naiss,
                    date_deces=date_deces,
                )
            )

    # Bulk create all instances
    with transaction.atomic():
        INSEEPatient.objects.bulk_create(patients_to_create)


if __name__ == "__main__":
    try:
        date_du_jour = datetime.now().strftime("%d%m%Y")
        file_path = Path(f"../deces_insee/deces_global_maj_{date_du_jour}.csv").resolve()
        import_data_from_csv(file_path)
        print("CSV Data import completed successfully.")

    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
