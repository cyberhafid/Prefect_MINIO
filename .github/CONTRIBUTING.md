# 🤝 Guide de contribution — Prefect_MINIO

Merci de l’intérêt porté au projet **Prefect_MINIO** 🚀  
Toutes les contributions sont les bienvenues : bugs, idées, améliorations, PR.

---

## ⚙️ Setup rapide

Ce projet utilise **uv** pour la gestion des dépendances.

```bash
git clone git@github.com:cyberhafid/Prefect_MINIO.git
cd Prefect_MINIO

uv sync --all-extras
source .venv/bin/activate  # Linux / macOS

🌿 Workflow de développement
1. Créer une branche

git checkout -b feat/ma-feature


2. Développer
Code dans src/
Docs dans docs/

3. Qualité du code
uv run ruff check . --fix
uv run pytest
4. Soumettre une PR
git push origin feat/ma-feature