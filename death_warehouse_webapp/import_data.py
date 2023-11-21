import os
import django
import csv
from datetime import datetime
from django.db import connections, DatabaseError
import logging

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "death_warehouse_webapp.settings")
django.setup()

from death_warehouse_app.models import INSEEPatient, WarehousePatient  
# Import data from CSV file
def import_data_from_csv(file_path):
    with open(file_path, 'r', encoding='latin-1', errors='ignore') as csvfile:  # Adjust encoding if needed
        reader = csv.DictReader(csvfile)

        for row in reader:
            nom = row.get('Nom', 'Nom manquant')
            prenom = row.get('Prenom', 'Prénom Manquant')
            date_naiss = row.get('Date de naissance', None)
            pays_naiss = row.get('Pays de naissance', 'Pays de naissance manquant')
            lieu_naiss = row.get('Lieu de naissance', 'Lieu de naissance manquant')
            code_naiss = row.get('Code lieu de naissance', '00000')
            date_deces = row.get('Date de deces', None)

            if date_naiss:
                try:
                    date_naiss = datetime.strptime(date_naiss, '%Y/%m/%d').date()
                except ValueError:
                    date_naiss = None
            
            if date_deces:
                try:
                    date_deces = datetime.strptime(date_deces, '%Y/%m/%d').date()
                except ValueError:
                    date_deces = None

            INSEEPatient.objects.update_or_create(
                nom=nom,
                prenom=prenom,
                defaults={
                    'date_naiss': date_naiss,
                    'pays_naiss': pays_naiss,
                    'lieu_naiss': lieu_naiss,
                    'code_naiss': code_naiss,
                    'date_deces': date_deces,
                }
            )

# Import data from SQL query
def import_data_from_db():
    logger = logging.getLogger(__name__)

    try:
        with connections['my_oracle'].cursor() as cursor:
            cursor.execute("""
                    SELECT
                        p.PATIENT_NUM,
                        p.LASTNAME,
                        p.FIRSTNAME,
                        p.BIRTH_DATE,
                        p.SEX,
                        p.MAIDEN_NAME,
                        p.DEATH_DATE,
                        p.BIRTH_COUNTRY,
                        MAX(i.HOSPITAL_PATIENT_ID) AS HOSPITAL_PATIENT_ID
                    FROM DWH.DWH_PATIENT p
                    JOIN DWH.DWH_PATIENT_IPPHIST i ON p.PATIENT_NUM = i.PATIENT_NUM
                    WHERE p.DEATH_DATE IS NOT NULL
                    GROUP BY p.PATIENT_NUM, p.LASTNAME, p.FIRSTNAME, p.BIRTH_DATE, p.SEX, p.MAIDEN_NAME, p.DEATH_DATE, p.BIRTH_COUNTRY
            """)
            data = cursor.fetchall()

            for row in data:
                WarehousePatient.objects.update_or_create(
                    PATIENT_NUM=row[0],
                    defaults={
                        'LASTNAME': row[1],
                        'FIRSTNAME': row[2],
                        'BIRTH_DATE': row[3],
                        'SEX': row[4],
                        'MAIDEN_NAME': row[5],
                        'DEATH_DATE': row[6],
                        'BIRTH_COUNTRY': row[7],
                        'HOSPITAL_PATIENT_ID': row[8],
                    }
                )

        logger.info("Data imported successfully.")
    except DatabaseError as e:
        logger.error(f"Database error occurred: {e}")

if __name__ == "__main__":
    try:
        date_du_jour = datetime.now().strftime("%d%m%Y")
        file_path = os.path.abspath(f"../deces_insee/deces_global_maj_{date_du_jour}.csv")
        import_data_from_csv(file_path)
        print("CSV Data import completed successfully.")

        import_data_from_db()
        print("SQL Data import completed successfully.")
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
