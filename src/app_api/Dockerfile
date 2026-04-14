# Utilisation d'une image Debian plus récente (2026)
FROM python:3.11-slim-bookworm

# 1. Installation de uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. On indique à uv d'utiliser le Python système (pas de venv)
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# 3. Copie des fichiers de dépendances
# uv privilégiera le uv.lock s'il existe pour garantir l'immutabilité
COPY pyproject.toml uv.lock ./

# 4. Installation des dépendances
# RUN uv pip install --system --no-cache uvicorn fastapi boto3 dotenv mlflow pandas setuptools protobuf
RUN uv pip install --system --no-cache -r pyproject.toml

# 5. Copie du code source
COPY . .

# 6. Exposition du port (optionnel mais recommandé pour la clarté)
EXPOSE ${FASTAPI_PORT:-8000}

# 7. Lancement de l'API
CMD ["python", "-m", "main", "--host", "0.0.0.0"]