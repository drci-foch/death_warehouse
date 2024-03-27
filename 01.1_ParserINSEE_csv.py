import os
import csv
from datetime import datetime

# Adjust the dossier to point to your CSV files location
dossier = "./deces_insee/"
donnees_globales = []

def extraire_informations(row):
    # Assuming CSV structure matches the final CSV output's headers
    nom_prenom = row['nomprenom'].split('*')
    nom = nom_prenom[0]
    prenom = nom_prenom[1].replace("/", "") if len(nom_prenom) > 1 else ""
    date_naissance = row['datenaiss']
    pays_naissance = row['paysnaiss'] or 'Pas enregistré'
    lieu_naissance = row['lieunaiss'] or 'Pas enregistré'
    code_lieu_naissance = row['commnaiss'] or '00000'
    date_deces = row['datedeces'] or '1970-01-01'
    code_deces = row['actedeces'] or '00000'
    
    # Conversion de date reste identique, juste mettre à jour les variables utilisées
    # Convertir date_naissance et date_deces comme dans le script original
    
    return {
        'Nom': nom,
        'Prenom': prenom,
        'Date de naissance': date_naissance,  # Supposant que la conversion de date est faite ici
        'Pays de naissance': pays_naissance,
        'Lieu de naissance': lieu_naissance,
        'Code lieu de naissance': code_lieu_naissance,
        'Date de deces': date_deces,  # Supposant que la conversion de date est faite ici
        'Code du lieu de deces': code_deces
    }

for fichier in os.listdir(dossier):
    if fichier.endswith(".csv"):  # Change to look for .csv files
        chemin_fichier = os.path.join(dossier, fichier)
        with open(chemin_fichier, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                print(row)
                informations = extraire_informations(row)
                print(informations)
                donnees_globales.append(informations)

# Writing to a new CSV remains the same
date_du_jour = datetime.now().strftime("%d%m%Y")
fichier_csv = f".//deces_insee/deces_global_maj_{date_du_jour}.csv"

with open(fichier_csv, 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.DictWriter(csvfile, fieldnames=donnees_globales[0].keys())
    csvwriter.writeheader()
    for personne in donnees_globales:
        csvwriter.writerow(personne)

print(f"L'étape 01_ParserINSEE a été réalisée avec succès")
