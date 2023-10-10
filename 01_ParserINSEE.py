import os
import csv
from datetime import datetime

characters = "/"
dossier = ".//deces_insee/"
donnees_globales = []

# Fonction pour extraire les informations d'une ligne
def extraire_informations(ligne):
    nom = ligne[0:79].strip().split('*')[0]
    prenom = ligne[0:79].strip().split('*')[-1].replace(characters, "")
    date_naissance = ligne[81:89].strip()
    code_lieu_naissance = ligne[89:94].strip() 
    lieu_naissance = ligne[94:123].strip()
    pays_naissance = ligne[124:153].strip()
    date_deces = ligne[154:162].strip()
    code_deces = ligne[163:168].strip()
    
    return {
        'Nom': nom,
        'Prenom': prenom,
        'Date de naissance': date_naissance,
        'Pays de naissance' : pays_naissance,
        'Lieu de naissance': lieu_naissance,
        'Code lieu de naissance': code_lieu_naissance,
        'Date de deces': date_deces,
        'Code du lieu de deces': code_deces
    }

# Parcourir les fichiers dans le dossier
for fichier in os.listdir(dossier):
    if fichier.endswith(".txt"): 
        chemin_fichier = os.path.join(dossier, fichier)
        
        with open(chemin_fichier, 'r', encoding='latin-1') as f:
            lignes = f.readlines()
            
            for ligne in lignes:
                if len(ligne) >= 176:  # Vérifier que la ligne a la longueur attendue
                    informations = extraire_informations(ligne)
                    donnees_globales.append(informations)

date_du_jour = datetime.now().strftime("%Y%m%d")
fichier_csv = f".//deces_insee/deces_global_maj_{date_du_jour}.csv"

with open(fichier_csv, 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.DictWriter(csvfile, fieldnames=donnees_globales[0].keys())
    csvwriter.writeheader()
    for personne in donnees_globales:
        csvwriter.writerow(personne)

print(f"L'étape 01_ParserINSEE a été réalisée avec succès")
