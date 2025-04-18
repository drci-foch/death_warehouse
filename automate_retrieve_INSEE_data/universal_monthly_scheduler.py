#!/usr/bin/env python3
"""
Planificateur mensuel universel
Ce script exécute une liste de scripts une fois par mois, compatible Windows et Linux.
Il utilise uniquement la bibliothèque standard Python.

Pour l'utiliser:
1. Configurez vos scripts dans la liste SCRIPTS_TO_RUN
2. Lancez ce script une fois, il s'autodémarrera en arrière-plan
3. Il s'exécutera automatiquement le premier jour de chaque mois

Pour arrêter le service: créez un fichier nommé "stop_scheduler" dans le même dossier
"""

import atexit
import datetime
import logging
import os  # Nécessaire pour certaines opérations non couvertes par pathlib
import platform
import subprocess
import sys
import time
import traceback
from pathlib import Path

# Configuration
SCRIPTS_TO_RUN = [
    "./retrieve_insee_data/00_RetrieveAutomaticFile.py",
    "./retrieve_insee_data/01_ParserINSEE.py",
    "./retrieve_insee_data/import_data.py",
]

# Scripts d'initialisation (peuvent être différents de SCRIPTS_TO_RUN)
INIT_SCRIPTS = [
    "./retrieve_insee_data/01.1_ParserINSEE.py",
    "./retrieve_insee_data/import_data.py",
]

# Répertoire de base (dossier contenant ce script)
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
PID_FILE = BASE_DIR / "scheduler.pid"
STOP_FILE = BASE_DIR / "stop_scheduler"
INIT_FLAG_FILE = BASE_DIR / "init_completed"

# Créer le dossier de logs s'il n'existe pas
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True)

# Configurer la journalisation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "scheduler.log"),
        logging.StreamHandler(),
    ],
)


def run_script(script_path):
    """Exécute un script Python et journalise le résultat"""
    full_path = BASE_DIR / script_path

    if not full_path.exists():
        logging.error(f"Le script {full_path} n'existe pas.")
        return False

    try:
        logging.info(f"Exécution du script: {script_path}")
        process = subprocess.run([sys.executable, str(full_path)], capture_output=True, text=True)

        # Journaliser la sortie
        if process.stdout:
            logging.info(f"Sortie de {script_path}:\n{process.stdout}")
        if process.stderr:
            logging.error(f"Erreurs de {script_path}:\n{process.stderr}")

        if process.returncode != 0:
            logging.error(f"Échec du script {script_path} (code {process.returncode})")
            return False

        logging.info(f"Script {script_path} exécuté avec succès")
        return True

    except Exception as e:
        logging.error(f"Erreur lors de l'exécution de {script_path}: {str(e)}")
        logging.error(traceback.format_exc())
        return False


def is_first_day_of_month():
    """Vérifie si c'est le premier jour du mois"""
    return datetime.datetime.now().day == 1


def time_until_next_execution():
    """Calcule le temps restant jusqu'à la prochaine exécution (en secondes)"""
    now = datetime.datetime.now()

    # Si nous sommes le premier jour du mois et qu'il est avant 2h du matin
    if now.day == 1 and now.hour < 2:
        next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
    else:
        # Calculer le premier jour du mois prochain
        if now.month == 12:
            next_month = 1
            next_year = now.year + 1
        else:
            next_month = now.month + 1
            next_year = now.year

        next_run = datetime.datetime(next_year, next_month, 1, 2, 0, 0)

    # Calculer la différence en secondes
    delta = next_run - now
    return delta.total_seconds()


def write_pid_file():
    """Écrit le PID dans un fichier"""
    PID_FILE.write_text(str(os.getpid()))


def remove_pid_file():
    """Supprime le fichier PID lors de la sortie"""
    if PID_FILE.exists():
        PID_FILE.unlink()


def run_monthly_tasks():
    """Exécute tous les scripts configurés"""
    logging.info(f"=== Début de l'exécution mensuelle {datetime.datetime.now()} ===")

    success_count = 0
    failure_count = 0

    for script in SCRIPTS_TO_RUN:
        if run_script(script):
            success_count += 1
        else:
            failure_count += 1

    logging.info(f"=== Fin de l'exécution: {success_count} réussis, {failure_count} échoués ===")


def run_init_tasks():
    """Exécute les scripts d'initialisation"""
    logging.info(f"=== Début de l'initialisation de la base {datetime.datetime.now()} ===")

    success_count = 0
    failure_count = 0

    for script in INIT_SCRIPTS:
        if run_script(script):
            success_count += 1
        else:
            failure_count += 1

    logging.info(f"=== Fin de l'initialisation: {success_count} réussis, {failure_count} échoués ===")

    # Créer le fichier d'initialisation complétée
    INIT_FLAG_FILE.write_text(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def daemonize():
    """Transforme le processus en daemon (uniquement sous Unix)"""
    if platform.system() == "Windows":
        return  # Windows n'a pas de concept de daemon comme Unix

    try:
        # Premier fork
        pid = os.fork()
        if pid > 0:
            # Quitter le processus parent
            sys.exit(0)
    except OSError:
        logging.error("Fork #1 a échoué")
        sys.exit(1)

    # Se détacher de l'environnement parent
    os.chdir("/")
    os.setsid()
    os.umask(0)

    try:
        # Second fork
        pid = os.fork()
        if pid > 0:
            # Quitter le processus parent
            sys.exit(0)
    except OSError:
        logging.error("Fork #2 a échoué")
        sys.exit(1)

    # Rediriger les descripteurs de fichiers standard
    sys.stdout.flush()
    sys.stderr.flush()

    with open(os.devnull) as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(LOG_DIR / "stdout.log", "a+") as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(LOG_DIR / "stderr.log", "a+") as f:
        os.dup2(f.fileno(), sys.stderr.fileno())


def check_already_running() -> bool:
    """Vérifie si le script est déjà en cours d'exécution"""
    if PID_FILE.exists():
        old_pid = PID_FILE.read_text().strip()

        # Vérifier si le processus existe toujours
        try:
            if platform.system() == "Windows":
                # Windows: utiliser tasklist pour vérifier si le PID existe
                check_cmd = f'tasklist /FI "PID eq {old_pid}" /NH'
                result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
                if old_pid in result.stdout:
                    return True
            else:
                # Unix: envoyer signal 0 pour vérifier si le processus existe
                os.kill(int(old_pid), 0)
                return True
        except (OSError, subprocess.SubprocessError):
            # Le processus n'existe plus
            PID_FILE.unlink()

    return False


def ask_initialization():
    """Demande à l'utilisateur s'il s'agit d'une première initialisation"""
    # Si le fichier d'initialisation existe déjà, pas besoin de demander
    if INIT_FLAG_FILE.exists():
        return False

    while True:
        response = input("Est-ce une première initialisation de la base ? (oui/non): ").lower().strip()
        if response in ["oui", "o", "yes", "y"]:
            return True
        elif response in ["non", "n", "no"]:
            # Créer le fichier d'initialisation pour ne pas redemander la prochaine fois
            INIT_FLAG_FILE.write_text(
                f"Initialisation ignorée: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            return False
        else:
            print("Veuillez répondre par 'oui' ou 'non'.")


def main():
    """Fonction principale du planificateur"""

    # Vérifier si le script est déjà en cours d'exécution
    if check_already_running():
        print(f"Le planificateur est déjà en cours d'exécution (PID: {PID_FILE.read_text().strip()})")
        sys.exit(1)

    # Demander s'il s'agit d'une première initialisation
    init_required = ask_initialization()

    # Enregistrer le handler de nettoyage
    atexit.register(remove_pid_file)

    # Si initialisation requise, exécuter les scripts d'initialisation avant de continuer
    if init_required:
        run_init_tasks()
        print("Initialisation terminée. Démarrage du planificateur mensuel...")

    # Devenir un daemon sous Unix
    if platform.system() != "Windows":
        print("Démarrage en arrière-plan...")
        daemonize()

    # Écrire le PID
    write_pid_file()

    logging.info(f"Planificateur démarré (PID: {os.getpid()})")

    try:
        while True:
            # Vérifier si le fichier d'arrêt existe
            if STOP_FILE.exists():
                logging.info("Fichier d'arrêt détecté, arrêt du planificateur...")
                STOP_FILE.unlink()
                break

            # Exécuter les tâches si c'est le premier jour du mois après 2h du matin
            now = datetime.datetime.now()
            if is_first_day_of_month() and now.hour >= 2:
                run_monthly_tasks()

                # Attendre jusqu'au mois prochain (pour éviter de ré-exécuter aujourd'hui)
                sleep_time = time_until_next_execution()
                logging.info(f"Attente jusqu'à la prochaine exécution: {sleep_time / 3600:.1f} heures")

                # Vérifier le fichier d'arrêt toutes les 5 minutes
                while sleep_time > 0:
                    time.sleep(min(300, sleep_time))  # 5 minutes ou moins
                    sleep_time -= 300

                    if STOP_FILE.exists():
                        logging.info("Fichier d'arrêt détecté, arrêt du planificateur...")
                        STOP_FILE.unlink()
                        return
            else:
                # Calculer le temps jusqu'à la prochaine exécution
                sleep_time = time_until_next_execution()
                logging.info(f"Prochaine exécution dans {sleep_time / 3600:.1f} heures")

                # Vérifier le fichier d'arrêt toutes les 5 minutes
                while sleep_time > 0:
                    time.sleep(min(300, sleep_time))  # 5 minutes ou moins
                    sleep_time -= 300

                    if STOP_FILE.exists():
                        logging.info("Fichier d'arrêt détecté, arrêt du planificateur...")
                        STOP_FILE.unlink()
                        return

    except KeyboardInterrupt:
        logging.info("Arrêt par l'utilisateur (Ctrl+C)")
    except Exception as e:
        logging.error(f"Erreur non gérée: {str(e)}")
        logging.error(traceback.format_exc())
    finally:
        logging.info("Planificateur arrêté")


if __name__ == "__main__":
    main()
