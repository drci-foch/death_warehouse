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
import os
import platform
import subprocess
import sys
import time
import traceback

# Configuration
SCRIPTS_TO_RUN = [
    "./retrieve_insee_data/00_RetrieveAutomaticFile.py",
    "./retrieve_insee_data/01_ParserINSEE.py",
    "../deathwarehouse_app/import_data.py",
]

# Répertoire de base (dossier contenant ce script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
PID_FILE = os.path.join(BASE_DIR, "scheduler.pid")
STOP_FILE = os.path.join(BASE_DIR, "stop_scheduler")

# Créer le dossier de logs s'il n'existe pas
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configurer la journalisation
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "scheduler.log")),
        logging.StreamHandler(),
    ],
)


def run_script(script_path):
    """Exécute un script Python et journalise le résultat"""
    full_path = os.path.join(BASE_DIR, script_path)

    if not os.path.exists(full_path):
        logging.error(f"Le script {full_path} n'existe pas.")
        return False

    try:
        logging.info(f"Exécution du script: {script_path}")
        process = subprocess.run([sys.executable, full_path], capture_output=True, text=True)

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
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_pid_file():
    """Supprime le fichier PID lors de la sortie"""
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


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
    with open(os.path.join(LOG_DIR, "stdout.log"), "a+") as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
    with open(os.path.join(LOG_DIR, "stderr.log"), "a+") as f:
        os.dup2(f.fileno(), sys.stderr.fileno())


def check_already_running():
    """Vérifie si le script est déjà en cours d'exécution"""
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            old_pid = f.read().strip()

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
            os.remove(PID_FILE)

    return False


def main():
    """Fonction principale du planificateur"""

    # Vérifier si le script est déjà en cours d'exécution
    if check_already_running():
        print(f"Le planificateur est déjà en cours d'exécution (PID: {open(PID_FILE).read().strip()})")
        sys.exit(1)

    # Enregistrer le handler de nettoyage
    atexit.register(remove_pid_file)

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
            if os.path.exists(STOP_FILE):
                logging.info("Fichier d'arrêt détecté, arrêt du planificateur...")
                os.remove(STOP_FILE)
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

                    if os.path.exists(STOP_FILE):
                        logging.info("Fichier d'arrêt détecté, arrêt du planificateur...")
                        os.remove(STOP_FILE)
                        return
            else:
                # Calculer le temps jusqu'à la prochaine exécution
                sleep_time = time_until_next_execution()
                logging.info(f"Prochaine exécution dans {sleep_time / 3600:.1f} heures")

                # Vérifier le fichier d'arrêt toutes les 5 minutes
                while sleep_time > 0:
                    time.sleep(min(300, sleep_time))  # 5 minutes ou moins
                    sleep_time -= 300

                    if os.path.exists(STOP_FILE):
                        logging.info("Fichier d'arrêt détecté, arrêt du planificateur...")
                        os.remove(STOP_FILE)
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
