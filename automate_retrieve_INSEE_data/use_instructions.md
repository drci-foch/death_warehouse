# Comment utiliser le planificateur universel

## Installation

1. **Téléchargez le script** dans le dossier où se trouvent les scripts que vous voulez exécuter
2. **Assurez-vous qu'il est exécutable**
   - Sur Linux/Mac : `chmod +x universal_monthly_scheduler.py`

## Configuration

1. **Ouvrez le script** avec un éditeur de texte et modifiez la section `SCRIPTS_TO_RUN` pour inclure les noms des scripts que vous voulez exécuter :
   ```python
   SCRIPTS_TO_RUN = [
       "script1.py",      # Remplacez par vos noms de scripts réels
       "script2.py",
       "import_insee.py",
       # Ajoutez autant de scripts que nécessaire
   ]
   ```

2. **Vérifiez que vos scripts sont dans le même dossier** que le planificateur ou spécifiez le chemin complet.

## Lancement

Pour démarrer le planificateur, exécutez simplement :
```
python universal_monthly_scheduler.py
```

- Sur Windows, le script continuera à s'exécuter dans votre invite de commande
- Sur Linux/Mac, le script se transformera automatiquement en démon (tâche d'arrière-plan)

## Fonctionnement

- Le script s'exécutera automatiquement le premier jour de chaque mois à 2h00 du matin
- Il créera un dossier `logs` contenant tous les journaux d'exécution
- Il vérifiera toutes les 5 minutes s'il est temps de s'exécuter ou s'il doit s'arrêter

## Arrêt du planificateur

Pour arrêter le planificateur, créez simplement un fichier vide nommé `stop_scheduler` dans le même dossier. Le planificateur détectera ce fichier et s'arrêtera proprement.

Sur Linux/Mac :
```
touch stop_scheduler
```

Sur Windows :
```
echo. > stop_scheduler
```

## Vérification

Pour vérifier si le planificateur est en cours d'exécution :
- Sur Windows, cherchez le processus Python dans le Gestionnaire des tâches
- Sur Linux/Mac, utilisez `ps aux | grep monthly_scheduler`
- Ou consultez le fichier `scheduler.pid` qui contient l'ID du processus

## Dépannage

Si vous rencontrez des problèmes :
1. Vérifiez les fichiers journaux dans le dossier `logs`
2. Assurez-vous que vos scripts fonctionnent correctement en les exécutant manuellement
3. Vérifiez les permissions d'exécution sur le script et le dossier de journaux