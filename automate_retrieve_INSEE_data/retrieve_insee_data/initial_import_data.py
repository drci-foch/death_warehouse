import csv
import gc
import os
import sys
from datetime import datetime
from pathlib import Path

import django
from django.db import connection, transaction
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

    # Use raw SQL for faster deletion
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM death_warehouse_app_inseepatient")
        logger.info("Deleted all existing records")

    batch_size = 10000  # Larger batch size
    patients_to_create = []
    row_count = 0
    error_count = 0
    batch_count = 0

    logger.info("Reading CSV file...")
    with open(file_path, encoding="latin-1", errors="ignore") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row_count += 1

            # Process row data
            nom = row.get("Nom", "Nom manquant")
            prenom = row.get("Prenom", "Prénom Manquant")
            date_naiss = row.get("Date de naissance", None)
            pays_naiss = row.get("Pays de naissance", "Pays de naissance manquant")
            lieu_naiss = row.get("Lieu de naissance", "Lieu de naissance manquant")
            code_naiss = row.get("Code lieu de naissance", "00000")
            date_deces = row.get("Date de deces", None)

            # Convert dates
            if date_naiss:
                try:
                    date_naiss = datetime.strptime(date_naiss, "%Y/%m/%d").date()
                except ValueError:
                    date_naiss = None
                    error_count += 1

            if date_deces:
                try:
                    date_deces = datetime.strptime(date_deces, "%Y/%m/%d").date()
                except ValueError:
                    date_deces = None
                    error_count += 1

            # Create patient object
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

            # Process in larger batches
            if len(patients_to_create) >= batch_size:
                batch_count += 1
                start_time = datetime.now()
                logger.info(f"Creating batch {batch_count} ({len(patients_to_create)} records)...")

                with transaction.atomic():
                    INSEEPatient.objects.bulk_create(patients_to_create)

                # Calculate and log performance metrics
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                records_per_second = len(patients_to_create) / duration if duration > 0 else 0

                logger.info(
                    f"Batch {batch_count} completed in {duration:.2f} seconds ({records_per_second:.1f} records/sec)"
                )
                logger.info(f"Total progress: {row_count} rows processed")

                # Clear the list and force garbage collection
                patients_to_create = []
                gc.collect()

    # Process remaining records
    if patients_to_create:
        batch_count += 1
        logger.info(f"Creating final batch {batch_count} ({len(patients_to_create)} records)...")

        with transaction.atomic():
            INSEEPatient.objects.bulk_create(patients_to_create)

    logger.success(f"Import completed: {row_count} total rows processed with {error_count} date errors")
    logger.info(f"Average batch size: {row_count / batch_count if batch_count > 0 else 0:.1f} records")


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
