# Auteur : Sarra Ben Yahia
# Description : Scraper pour automatiser la tâche de retéléchargement des nouveaux fichiers màj par l'INSEE
# TODO : Planifier le run

import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup


site_url = 'https://www.data.gouv.fr/fr/datasets/fichier-des-personnes-decedees/'
dossier_local = ".//deces_insee/"

# Créer le dossier local s'il n'existe pas
if not os.path.exists(dossier_local):
    os.makedirs(dossier_local)


def telecharger_fichier(url, dossier_local):
    nom_fichier = os.path.basename(url)
    chemin_local = os.path.join(dossier_local, nom_fichier)
    with open(chemin_local, 'wb') as fichier_local:
        response = requests.get(url, stream=True)
        for morceau in response.iter_content(1024):
            fichier_local.write(morceau)


def extraire_liens_fichiers(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    liens = []
    for lien in soup.find_all('a', href=True):
        lien_absolu = urljoin(site_url, lien['href'])
        liens.append(lien_absolu)
    return liens


liens_fichiers = extraire_liens_fichiers(site_url)
for lien in liens_fichiers:
    nom_fichier = os.path.basename(lien)
    # Vérifier si le fichier commence par "deces"
    if nom_fichier.startswith("deces"):
        chemin_local = os.path.join(dossier_local, nom_fichier)
        # Vérifier si le fichier existe déjà localement
        if not os.path.exists(chemin_local):
            print(f'Téléchargement de {nom_fichier}...')
            telecharger_fichier(lien, dossier_local)
        else:
            print(f'{nom_fichier} existe déjà localement. Passer au fichier suivant.')

print(f"L'étape 00_RetrieveAutomaticFile a été réalisée avec succès")
