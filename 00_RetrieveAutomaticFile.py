import os
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from urllib.parse import urljoin
from time import sleep

# URL of the website to scrape
site_url = 'https://www.data.gouv.fr/fr/datasets/fichier-des-personnes-decedees/'
# Local directory to save downloaded files
dossier_local = "./deces_insee/"

# Create the local directory if it does not exist
if not os.path.exists(dossier_local):
    os.makedirs(dossier_local)

# Configure Edge for Selenium with automatic download settings
options = Options()
options.use_chromium = True
prefs = {
    "download.default_directory": os.path.abspath(dossier_local),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

# Initialize the Edge driver
edge_service = Service('C:/Users/benysar/Downloads/edgedriver_win64/msedgedriver.exe')  # Replace with your Edge WebDriver path
driver = webdriver.Edge(service=edge_service, options=options)

def extraire_liens_fichiers(url):
    driver.get(url)
    sleep(5)  # Wait for the page to load
    liens = []
    elements_lien = driver.find_elements(By.TAG_NAME, 'a')
    for element in elements_lien:
        lien = element.get_attribute('href')
        if lien and lien.endswith('.txt'):  # Modify this condition based on actual file extensions
            liens.append(lien)
    return liens

# Extract file links and download files
liens_fichiers = extraire_liens_fichiers(site_url)
for lien in liens_fichiers:
    nom_fichier = os.path.basename(lien)
    if nom_fichier.startswith("deces"):
        chemin_local = os.path.join(dossier_local, nom_fichier)
        if not os.path.exists(chemin_local):
            print(f'Téléchargement de {nom_fichier}...')
            driver.get(lien)  # Navigate to each download link
            sleep(2)  # Wait for a bit to allow the download to start
        else:
            print(f'{nom_fichier} existe déjà localement. Passer au fichier suivant.')

# Close the browser once done
driver.quit()
print(f"L'étape 00_RetrieveAutomaticFile a été réalisée avec succès")
