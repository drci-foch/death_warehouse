import requests
import os

# URL de l'API du dataset
dataset_url = "https://www.data.gouv.fr/api/1/datasets/fichier-des-personnes-decedees/"

# Requête GET pour récupérer les métadonnées du dataset
response = requests.get(dataset_url)
dataset_info = response.json()

# Trouver la ressource la plus récente
latest_resource = None
for resource in dataset_info['resources']:
    if latest_resource is None or resource['created_at'] > latest_resource['created_at']:
        latest_resource = resource

if latest_resource:
    # URL du fichier le plus récent
    file_url = latest_resource['url']
    file_name = file_url.split("/")[-1]

    # Requête GET pour télécharger le fichier
    file_response = requests.get(file_url)

    # Vérifier que la requête a réussi
    if file_response.status_code == 200:
        # Créer le dossier "deces_insee" s'il n'existe pas déjà
        directory = "deces_insee"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Chemin complet pour sauvegarder le fichier localement dans le dossier "deces_insee"
        local_path = os.path.join(directory, file_name)

        # Écrire le contenu du fichier téléchargé dans un fichier local
        with open(local_path, 'w', encoding='utf-8') as file:
            file.write(file_response.text)

        print(f"Fichier téléchargé et sauvegardé sous: {local_path}")

        # Afficher les premières lignes du fichier
        with open(local_path, 'r', encoding='utf-8') as file:
            for _ in range(10):
                print(file.readline().strip())
    else:
        print("Erreur lors du téléchargement du fichier")
else:
    print("Aucune ressource trouvée dans le dataset")