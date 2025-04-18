import csv
import logging
import os
from datetime import datetime
from pathlib import Path

import django

from death_warehouse_webapp.death_warehouse_app.models import INSEEPatient

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "death_warehouse_webapp.settings")
django.setup()
logger = logging.getLogger(__name__)


def bulk_import_data_from_csv(file_path, batch_size=1000):
    with open(file_path, encoding="latin-1", errors="ignore") as csvfile:
        reader = csv.DictReader(csvfile)
        objects_list = []
        total_imported = 0  # Keep track of the total number of imported records

        for row in reader:
            nom = row.get("Nom", "Nom manquant")
            prenom = row.get("Prenom", "Prénom Manquant")
            date_naiss = row.get("Date de naissance", None)
            pays_naiss = row.get("Pays de naissance", "Pays de naissance manquant")
            lieu_naiss = row.get("Lieu de naissance", "Lieu de naissance manquant")
            code_naiss = row.get("Code lieu de naissance", "00000")
            date_deces = row.get("Date de deces", None)

            # Process dates
            if date_naiss:
                try:
                    date_naiss = datetime.strptime(date_naiss, "%Y/%m/%d").date()
                except ValueError:
                    logger.warning(f"Invalid date_naiss format for {nom} {prenom}. Skipping record.")
                    continue
            else:
                logger.warning(f"Missing date_naiss for {nom} {prenom}. Skipping record.")
                continue

            if date_deces:
                try:
                    date_deces = datetime.strptime(date_deces, "%Y/%m/%d").date()
                except ValueError:
                    date_deces = None

            # Prepare model instance
            instance = INSEEPatient(
                nom=nom,
                prenom=prenom,
                date_naiss=date_naiss,
                pays_naiss=pays_naiss,
                lieu_naiss=lieu_naiss,
                code_naiss=code_naiss,
                date_deces=date_deces,
            )
            objects_list.append(instance)

            if len(objects_list) >= batch_size:
                INSEEPatient.objects.bulk_create(objects_list, ignore_conflicts=True)
                total_imported += len(objects_list)
                print(f"Processed a batch of {len(objects_list)} records. Total processed: {total_imported}.")
                objects_list = []

        if objects_list:  # For the last batch which might be less than batch_size
            INSEEPatient.objects.bulk_create(objects_list, ignore_conflicts=True)
            total_imported += len(objects_list)
            print(f"Processed the final batch of {len(objects_list)} records. Total processed: {total_imported}.")

        # Insert any remaining objects
        if objects_list:
            INSEEPatient.objects.bulk_create(objects_list, ignore_conflicts=True)


if __name__ == "__main__":
    try:
        date_du_jour = datetime.now().strftime("%d%m%Y")
        file_path = Path(f"./deces_global_maj_{date_du_jour}.csv").resolve()
        bulk_import_data_from_csv(file_path)
        print("CSV Data import completed successfully.")

    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
