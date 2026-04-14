# 🚀 Prefect_MINIO — MLOps Factory

Ce projet est une plateforme de Machine Learning industrialisée basée sur une architecture micro-services.  
Elle permet de gérer le cycle de vie complet d’un modèle : de l’entraînement au suivi des métriques jusqu’à l’exposition via une API et une interface utilisateur.

👉 Projet maintenu par **cyberhafid**  
👉 Version actuelle : **0.1.1**

---

[![Code](https://img.shields.io/badge/Code-0.1.1-181717?logo=github)](https://github.com/cyberhafid/Prefect_MINIO)  
![Python](https://img.shields.io/badge/python-3.11-blue.svg)  
![Docker](https://img.shields.io/badge/docker-ready-blue.svg?logo=docker)  
![License](https://img.shields.io/badge/license-MIT-green.svg)  
![Repo Size](https://img.shields.io/github/repo-size/cyberhafid/Prefect_MINIO)  
![Last Commit](https://img.shields.io/github/last-commit/cyberhafid/Prefect_MINIO)  
![Open Issues](https://img.shields.io/github/issues/cyberhafid/Prefect_MINIO)

---

## 📦 Repository


git clone git@github.com:cyberhafid/Prefect_MINIO.git
cd Prefect_MINIO

## 🏗️ Architecture du Système

L'infrastructure est entièrement conteneurisée avec **Docker Compose** et repose sur :

- **MLflow** → tracking & registry des modèles  
- **MinIO** → stockage des artefacts (S3-compatible)  
- **FastAPI** → API de prédiction  
- **Streamlit** → interface utilisateur  

---

## ⚙️ Installation rapide

### 1. Préparer l’environnement
```bash
(cd src/app_train && uv sync)





2. Créer les réseaux Docker
docker network create monitoring-networkdocker network create prefect-network

3. Lancer les services
docker compose up --build -d

🧠 Entraînement du modèle
(cd src/app_train && uv run python train.py --init)

🔄 Orchestration avec Prefect
prefect work-pool create "train-pool" --type dockerprefect worker start --pool 'train-pool'

📊 Monitoring


Prometheus → métriques


Grafana → dashboards


Uptime Kuma → disponibilité



🌐 Accès aux services
ServiceURLAPIhttp://localhost:8000Swaggerhttp://localhost:8000/docsStreamlithttp://localhost:8501MLflowhttp://localhost:5000MinIOhttp://localhost:9001Prefecthttp://localhost:4200Grafanahttp://localhost:3000

🔁 CI/CD
Le projet inclut :


✅ Tests automatisés (Pytest)


✅ Lint (Ruff)


✅ Scan sécurité (Gitleaks)


✅ Build Docker


✅ Documentation (Sphinx)



📂 Structure du projet
src/├── app_api/      # Backend FastAPI├── app_front/    # Frontend Streamlit└── app_train/    # Entraînement & Prefect

🔐 Variables d’environnement
Créer un fichier .env :
AWS_ACCESS_KEY_ID=xxxAWS_SECRET_ACCESS_KEY=xxxMLFLOW_TRACKING_URI=http://mlflow:5000MLFLOW_S3_ENDPOINT_URL=http://minio:9000

🐳 Commandes utiles
docker compose up -ddocker compose down -vdocker compose psdocker logs -f <container>

📌 Notes


Assure-toi que Docker est lancé


Lancement initial → nécessite création du premier modèle


Nettoie régulièrement les images Docker :


docker image prune -a

👨‍💻 Auteur
Projet maintenu par cyberhafid
Repo : https://github.com/cyberhafid/Prefect_MINIO
---Si tu veux, je peux te faire une version :- 💼 **:contentReference[oaicite:0]{index=0}**- 🌍 **:contentReference[oaicite:1]{index=1}**- 📊 ou avec **:contentReference[oaicite:2]{index=2}**Dis-moi 👍