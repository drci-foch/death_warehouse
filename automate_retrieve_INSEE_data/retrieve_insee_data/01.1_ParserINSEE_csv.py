import csv
from datetime import datetime
from pathlib import Path


# Function to convert date format from YYYYMMDD to YYYY/MM/DD
def convert_date_format(date_string):
    try:
        # Attempt to parse the date string
        date_object = datetime.strptime(date_string, "%Y%m%d")
    except ValueError:
        # If the parsing fails, set the date to default value
        date_object = datetime(1970, 1, 1)
    return date_object.strftime("%Y/%m/%d")


def extraire_informations(row):
    # Assuming CSV structure matches the final CSV output's headers
    nom_prenom = row["nomprenom"].split("*")
    nom = nom_prenom[0]
    prenom = nom_prenom[1].replace("/", "") if len(nom_prenom) > 1 else ""
    date_naissance = convert_date_format(row["datenaiss"])
    pays_naissance = row["paysnaiss"] or "Pas enregistré"
    lieu_naissance = row["lieunaiss"] or "Pas enregistré"
    code_lieu_naissance = row["commnaiss"] or "00000"
    date_deces = convert_date_format(row["datedeces"])
    code_deces = row["actedeces"] or "00000"

    return {
        "Nom": nom,
        "Prenom": prenom,
        "Date de naissance": date_naissance,
        "Pays de naissance": pays_naissance,
        "Lieu de naissance": lieu_naissance,
        "Code lieu de naissance": code_lieu_naissance,
        "Date de deces": date_deces,
        "Code du lieu de deces": code_deces,
    }


dossier = "../.././deces_insee/"
batch_size = 100


# Function to process files in batches
def process_files_in_batches(file_list, batch_size):
    for i in range(0, len(file_list), batch_size):
        batch_files = file_list[i : i + batch_size]
        process_batch(batch_files, i)


# Function to process a batch of files
def process_batch(batch_files, batch_index):
    donnees_globales = []
    for fichier in batch_files:
        chemin_fichier = Path(dossier) / fichier
        print(f"Processing file: {chemin_fichier}")
        with open(chemin_fichier, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            for row in reader:
                informations = extraire_informations(row)
                donnees_globales.append(informations)

    # Writing to a new CSV for this batch
    date_du_jour = datetime.now().strftime("%d%m%Y")
    fichier_csv = f"deces_global_maj_{date_du_jour}_batch_{batch_index}.csv"  # Updated path
    print(f"Writing to CSV file: {fichier_csv}")

    try:
        with open(fichier_csv, "w", newline="", encoding="utf-8") as csvfile:
            csvwriter = csv.DictWriter(csvfile, fieldnames=donnees_globales[0].keys())
            csvwriter.writeheader()
            for personne in donnees_globales:
                csvwriter.writerow(personne)
        print(f"CSV file '{fichier_csv}' has been successfully saved.")
    except Exception as e:
        print(f"An error occurred while saving the CSV file: {e}")


# Get list of CSV files
csv_files = [f for f in Path.iterdir(dossier) if f.endswith(".csv")]

# Process files in batches
process_files_in_batches(csv_files, batch_size)
