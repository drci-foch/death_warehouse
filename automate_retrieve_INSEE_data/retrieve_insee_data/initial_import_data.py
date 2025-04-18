import csv
import os
import sys
from datetime import datetime
from pathlib import Path

import django
from django.db import transaction
from loguru import logger

# Use relative paths based on the script location
script_path = Path(__file__).resolve()
script_dir = script_path.parent
base_dir = script_dir.parent.parent  # Go up to reach the base project directory
project_dir = base_dir / "death_warehouse_webapp"

# Add the django project directory to sys.path
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "death_warehouse_webapp.settings")

# Initialize Django
django.setup()

# Now import your model
from death_warehouse_app.models import INSEEPatient

# Configure loguru for better logging
logger.remove()  # Remove default handler
logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")
logger.add("import_insee.log", rotation="10 MB", level="DEBUG")

def import_data_from_csv(file_path):
    # Clear existing data
    logger.info(f"Starting import from {file_path}")
    logger.info("Deleting existing records...")
    deleted_count = INSEEPatient.objects.all().delete()
    logger.info(f"Deleted {deleted_count} existing records")

    patients_to_create = []
    row_count = 0
    error_count = 0

    logger.info("Reading CSV file...")
    with open(
        file_path, encoding="latin-1", errors="ignore"
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row_count += 1
            if row_count % 10000 == 0:
                logger.info(f"Processed {row_count} rows so far...")

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
                    error_count += 1
                    logger.warning(f"Invalid date format for date of birth: {row.get('Date de naissance')} at row {row_count}")

            if date_deces:
                try:
                    date_deces = datetime.strptime(date_deces, "%Y/%m/%d").date()
                except ValueError:
                    date_deces = None
                    error_count += 1
                    logger.warning(f"Invalid date format for death date: {row.get('Date de deces')} at row {row_count}")

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

            # Process in batches to avoid memory issues with large files
            if len(patients_to_create) >= 5000:
                logger.info(f"Bulk creating batch of {len(patients_to_create)} records...")
                with transaction.atomic():
                    INSEEPatient.objects.bulk_create(patients_to_create)
                patients_to_create = []

    # Bulk create remaining instances
    if patients_to_create:
        logger.info(f"Bulk creating final batch of {len(patients_to_create)} records...")
        with transaction.atomic():
            INSEEPatient.objects.bulk_create(patients_to_create)

    logger.success(f"Import completed: {row_count} total rows processed with {error_count} date errors")

if __name__ == "__main__":
    try:
        date_du_jour = datetime.now().strftime("%d%m%Y")
        file_path = Path(f"./deces_global_maj_{date_du_jour}.csv").resolve()
        import_data_from_csv(file_path)
        print("CSV Data import completed successfully.")

    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
