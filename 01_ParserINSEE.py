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

# Ouvrir le fichier CSV en mode lecture et créer un nouveau fichier CSV en mode écriture
with open(fichier_csv, 'r') as input_file, open(f".//deces_insee/global_death_final_{date_du_jour}.csv", 'w') as output_file:
    # Lire les lignes du fichier d'entrée
    lines = input_file.readlines()
    
    # Écrire l'en-tête du fichier de sortie
    output_file.write(lines[0])
    
    # Parcourir les lignes de données
    for line in lines[1:]:
        parts = line.strip().split(',')
        nom = parts[0]
        prenom = parts[1]
        date_naissance = parts[2]
        date_deces = parts[6]
        
        # Fonction pour formater la date
        def format_date(date_str):
            if date_str[:4] == '0000' or date_str[4:6] == '00' or date_str[6:8] == '00':
                return '1970-01-01'
            year = date_str[:4]
            month = date_str[4:6] if date_str[4:6] != '00' else '01'
            day = date_str[6:8] if date_str[6:8] != '00' else '01'
            return f'{year}-{month}-{day}'
        
        # Formater la date de naissance
        if date_naissance == '':
            date_naissance_formatee = ''
        else:
            date_naissance_formatee = format_date(date_naissance)
        
        # Formater la date de décès
        if date_deces == '':
            date_deces_formatee = ''
        else:
            date_deces_formatee = format_date(date_deces)
        
        
        # Écrire la ligne mise à jour dans le fichier de sortie
        output_file.write(f'{nom},{prenom},{date_naissance_formatee},{",".join(parts[3:6])},{date_deces_formatee},{",".join(parts[7:])}\n')
    
# Fermer les fichiers
input_file.close()
output_file.close()

print(f"L'étape 01_ParserINSEE a été réalisée avec succès")
