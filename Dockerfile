FROM python:3.12-slim-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Créer le répertoire pour la base de données avec les bonnes permissions
RUN mkdir -p /data/db && chmod 777 /data/db

# Écrire le fichier de configuration à la racine du projet
RUN mkdir -p /app && echo "/data/db/mydatabase" > /app/db_config.txt

# Vérifier que le fichier existe
RUN ls -la /app/db_config.txt

COPY ./death_warehouse_webapp ./death_warehouse_webapp
EXPOSE 8000
CMD ["python", "./death_warehouse_webapp/manage.py", "runserver", "0.0.0.0:8000"]