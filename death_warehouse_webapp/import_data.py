import os
import sys
import django
from datetime import datetime

# Remplacez 'nom_de_votre_projet.settings' par le nom de votre projet Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "death_warehouse_webapp.settings")

# Initialisez Django
django.setup()


import csv
from death_warehouse_app.models import RecherchePatient

def import_data_from_csv(file_path):
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            RecherchePatient.objects.create(
                nom=row['Nom'],
                prenom = row['Prenom'],
                date_naiss=row['Date de naissance'],
                pays_naiss = row['Pays de naissance'],
                lieu_naiss = row['Lieu de naissance'],
                code_naiss=row['Code lieu de naissance'],

            )

date_du_jour = datetime.now().strftime("%Y%m%d")
import_data_from_csv(os.path.abspath(f"../deces_insee/global_death_final_{date_du_jour}.csv"))
