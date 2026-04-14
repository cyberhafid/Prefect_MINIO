# Utilisation d'une version de Python plus récente et stable
FROM python:3.11-slim-bookworm

# 1. Installation de uv depuis l'image officielle
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. Configuration pour installer dans le Python système du conteneur
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# 3. Copie des fichiers de dépendances
# uv utilisera uv.lock pour figer les versions si le fichier est présent
COPY pyproject.toml uv.lock ./

# 4. Installation des dépendances via uv pip
# L'argument -r pyproject.toml permet de lire directement le fichier de projet
# RUN uv pip install --system --no-cache dotenv requests streamlit
RUN uv pip install --system --no-cache -r pyproject.toml

# 5. Copie du reste de l'application
COPY . .

# 6. Exposition du port par défaut de Streamlit
EXPOSE ${STREAMLIT_PORT:-8501}

# 7. Lancement de l'application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]