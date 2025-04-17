import os
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# URL of the website to scrape
site_url = "https://www.data.gouv.fr/fr/datasets/fichier-des-personnes-decedees/"

# Local directory to save downloaded files
dossier_local = "../.././deces_insee/"

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
    "safebrowsing.enabled": True,
}
options.add_experimental_option("prefs", prefs)

# Utilisation du WebDriver Manager
try:
    from selenium.webdriver.edge.service import Service as EdgeService
    from webdriver_manager.microsoft import EdgeChromiumDriverManager

    driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
except ImportError:
    # Si webdriver-manager n'est pas installé, utilisez le chemin vers msedgedriver.exe
    edge_driver_path = r"C:\path\to\msedgedriver.exe"
    driver = webdriver.Edge(service=Service(edge_driver_path), options=options)


def extraire_liens_fichiers(url):
    driver.get(url)
    print("Looking for data.gouv page")

    # Wait for the page to load completely
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
        print("Page loaded successfully!")

        # Attendre un peu plus pour s'assurer que la page est complètement chargée
        sleep(2)

        # Méthode sécurisée pour extraire les liens
        liens = []
        max_retries = 3

        # Utilisons une approche plus robuste - récupérer tous les liens d'un coup
        for retry in range(max_retries):
            try:
                # Exécuter du JavaScript pour obtenir tous les liens à la fois
                script = """
                const links = Array.from(document.getElementsByTagName('a'));
                return links
                    .filter(link => link.href && link.href.endsWith('.txt'))
                    .map(link => link.href);
                """
                liens = driver.execute_script(script)

                if liens:
                    print(f"Found {len(liens)} .txt links")
                    break
                else:
                    print(f"Retry {retry + 1}/{max_retries} - No links found yet")
                    sleep(1)
            except Exception as e:
                print(f"Error on attempt {retry + 1}: {e}")
                sleep(1)

        return liens
    except Exception as e:
        print(f"Error during page loading: {e}")
        return []


# Extract file links and download files
try:
    liens_fichiers = extraire_liens_fichiers(site_url)

    if not liens_fichiers:
        print("No .txt links found. Trying an alternative approach...")
        # Si aucun lien n'est trouvé, essayons de naviguer vers la page des ressources
        try:
            # Chercher un bouton ou lien pour accéder aux ressources
            resource_elements = driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'Ressources') or contains(text(), 'resources') or contains(text(), 'fichiers')]",
            )
            if resource_elements:
                for elem in resource_elements:
                    try:
                        print(f"Clicking on element: {elem.text}")
                        elem.click()
                        sleep(2)
                        # Essayer à nouveau d'extraire les liens
                        liens_fichiers = extraire_liens_fichiers(driver.current_url)
                        if liens_fichiers:
                            break
                    except:
                        continue
        except Exception as e:
            print(f"Alternative approach failed: {e}")

    print(f"Total links found: {len(liens_fichiers)}")
    for lien in liens_fichiers:
        nom_fichier = os.path.basename(lien)
        if nom_fichier.startswith("deces"):
            chemin_local = os.path.join(dossier_local, nom_fichier)
            if not os.path.exists(chemin_local):
                print(f"Téléchargement de {nom_fichier}...")
                driver.get(lien)  # Navigate to each download link
                sleep(3)  # Wait longer to ensure download starts
            else:
                print(f"{nom_fichier} existe déjà localement. Passer au fichier suivant.")
except Exception as e:
    print(f"Une erreur s'est produite: {e}")
finally:
    # Close the browser once done
    driver.quit()
    print("L'étape 00_RetrieveAutomaticFile a été terminée")
