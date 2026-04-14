import os
import sys

# Chemin vers la racine du projet
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Ajout dynamique des dossiers sources
sys.path.insert(0, os.path.join(root, "src/app_api"))
sys.path.insert(0, os.path.join(root, "src/app_front"))
sys.path.insert(0, os.path.join(root, "src/app_train"))
