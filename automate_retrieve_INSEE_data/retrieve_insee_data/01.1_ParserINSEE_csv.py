import csv
import zipfile
from datetime import datetime
from pathlib import Path


# Function to convert date format from YYYYMMDD to YYYY/MM/DD
def convert_date_format(date_string):
    try:
        # Attempt to parse the date string
        date_object = datetime.strptime(date_string, "%Y%m%d")
        return date_object.strftime("%Y/%m/%d")
    except ValueError:
        # If the parsing fails, set the date to default value
        return "1970/01/01"


def extraire_informations(row):
    # Assuming CSV structure matches the final CSV output's headers
    nom_prenom = row["nomprenom"].split("*") if "nomprenom" in row else ["Pas enregistré", ""]
    nom = nom_prenom[0]
    prenom = nom_prenom[1].replace("/", "") if len(nom_prenom) > 1 else ""

    date_naissance = convert_date_format(row.get("datenaiss", ""))
    pays_naissance = row.get("paysnaiss", "") or "Pas enregistré"
    lieu_naissance = row.get("lieunaiss", "") or "Pas enregistré"
    code_lieu_naissance = row.get("commnaiss", "") or "00000"
    date_deces = convert_date_format(row.get("datedeces", ""))
    code_deces = row.get("actedeces", "") or "00000"

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


# Function to process a single CSV file (either directly or from a zip)
def process_csv_file(file_path, is_zip=False):
    donnees = []

    if is_zip:
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            for csv_name in zip_ref.namelist():
                if csv_name.endswith(".csv"):
                    with zip_ref.open(csv_name) as csv_file:
                        # Need to decode bytes for CSV reader
                        text = csv_file.read().decode("utf-8")
                        reader = csv.DictReader(text.splitlines(), delimiter=";")
                        for row in reader:
                            informations = extraire_informations(row)
                            donnees.append(informations)
    else:
        with open(file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            for row in reader:
                informations = extraire_informations(row)
                donnees.append(informations)

    return donnees


# Function to process files in batches
def process_files_in_batches(dossier, batch_size):
    # Get list of files (both CSV and ZIP)
    dossier_path = Path(dossier)
    all_files = []

    for f in dossier_path.iterdir():
        if f.suffix.lower() in [".csv", ".zip"]:
            all_files.append(f)

    print(f"Found {len(all_files)} files to process")

    # Process in batches
    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i : i + batch_size]
        donnees_globales = []

        # Process each file in the batch
        for fichier in batch_files:
            print(f"Processing file: {fichier}")
            is_zip = fichier.suffix.lower() == ".zip"
            file_data = process_csv_file(fichier, is_zip)
            donnees_globales.extend(file_data)

        if donnees_globales:
            # Writing to a new CSV for this batch
            date_du_jour = datetime.now().strftime("%d%m%Y")
            fichier_csv = f"deces_global_maj_{date_du_jour}.csv"

            try:
                with open(fichier_csv, "w", newline="", encoding="utf-8") as csvfile:
                    csvwriter = csv.DictWriter(csvfile, fieldnames=donnees_globales[0].keys())
                    csvwriter.writeheader()
                    for personne in donnees_globales:
                        csvwriter.writerow(personne)
                print(f"CSV file '{fichier_csv}' has been successfully saved with {len(donnees_globales)} records.")
            except Exception as e:
                print(f"An error occurred while saving the CSV file: {e}")
        else:
            print(f"No data found in batch {i // batch_size}")


# Main execution
if __name__ == "__main__":
    dossier = ".././deces_insee/initial_import/"
    batch_size = 100
    process_files_in_batches(dossier, batch_size)
