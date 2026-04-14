# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
from unittest.mock import MagicMock


# On crée une classe qui accepte d'être utilisée avec "with"
class MagicContextManager(MagicMock):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# On configure le mock de streamlit
mock_st = MagicMock()
mock_st.sidebar = MagicContextManager()  # On donne le pouvoir du "with" à sidebar

# On force Python à utiliser ce mock au lieu de chercher la vraie librairie
sys.modules["streamlit"] = mock_st
sys.path.insert(0, os.path.abspath("../../"))
sys.path.insert(0, os.path.abspath("../../src"))

project = "Prefect_MINIO"
copyright = "2026, cyberhafid"
author = "cyberhafid"
release = "v0.1.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # INDISPENSABLE : extrait la doc des docstrings
    "sphinx.ext.napoleon",  # Supporte le format Google/NumPy (plus lisible)
    "sphinx.ext.viewcode",  # Ajoute un lien [source] à côté de tes fonctions
    "sphinx.ext.mathjax",  # Pour le rendu des formules LaTeX
    "myst_parser",  # Pour lire les fichiers .md (README, etc.)
    "sphinxcontrib.bibtex",  # Pour la gestion du fichier .bib
]
templates_path = ["_templates"]

bibtex_bibfiles = ["refs.bib"]
exclude_patterns = []

language = "fr"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#7C4DFF",
        "color-brand-content": "#7C4DFF",
    },
}

bibtex_default_style = "unsrt"

autodoc_mock_imports = [
    "boto3",
    "dotenv",
    "fastapi",
    "loguru",
    "mlflow",
    "pandas",
    "prometheus-client",
    "protobuf",
    "psutil",
    "setuptools",
    "uvicorn",
    "requests",
    "streamlit",
    "prefect",
    "prefect-docker",
    "scikit-learn",
    "sklearn",
    "modules",
    "prometheus_client",
    "app",
    "pydantic",
    "starlette",
]
