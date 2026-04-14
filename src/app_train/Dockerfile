# src/train/Dockerfile.worker
FROM prefecthq/prefect:3-python3.11

# Installation de 'uv'
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Définition du dossier de travail
RUN mkdir -p /train
WORKDIR /train

# Variables d'environnement pour que uv crée l'environnement virtuel directement dans le système
ENV UV_SYSTEM_PYTHON=1

# 1. Copier d'abord les fichiers de dépendances pour optimiser le cache Docker
COPY pyproject.toml ./

# 2. Installer les dépendances via uv (sans installer le projet en lui-même si pas nécessaire)
RUN uv pip install -r pyproject.toml

# 3. Copier tout le reste du code du dossier train/
COPY . /train

# Variables d'environnement critiques (peuvent aussi être passées via le docker-compose ou le déploiement)
ENV PYTHONPATH=/train

# Commande par défaut : Démarrer un Prefect Worker attaché au pool "my-docker-pool"
CMD ["prefect", "worker", "start", "--pool", "train-pool"]