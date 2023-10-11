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
            # Vérifiez chaque champ et définissez des valeurs par défaut si elles sont manquantes
            nom = row.get('Nom', 'Nom manquant')
            prenom = row.get('Prénom', 'Prénom Manquant')
            
            date_naiss = row.get('Date de naissance', None)
            if date_naiss:
                try:
                    date_naiss = datetime.strptime(date_naiss, '%Y-%m-%d')
                except ValueError:
                    date_naiss = None  # Remplacez par `None` si le format est incorrect
            
            pays_naiss = row.get('Pays de naissance', 'Pays de naissance manquant')
            lieu_naiss = row.get('Lieu de naissance', 'Lieu de naissance manquant')
            code_naiss = row.get('Code lieu de naissance', '00000')
            date_deces = row.get('Date de deces', None)
            
            if date_deces:
                try:
                    date_deces = datetime.strptime(date_deces, '%Y-%m-%d')
                except ValueError:
                    date_deces = '1970-01-01'  # Remplacez par `None` si le format est incorrect
            

            RecherchePatient.objects.create(
                nom=nom,
                prenom=prenom,
                date_naiss=date_naiss,
                pays_naiss=pays_naiss,
                lieu_naiss=lieu_naiss,
                code_naiss=code_naiss,
                date_deces=date_deces,

            )

date_du_jour = datetime.now().strftime("%Y%m%d")

import_data_from_csv(os.path.abspath(f"../deces_insee/global_death_final_{date_du_jour}.csv"))