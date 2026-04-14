import os
from typing import Optional, TypedDict

import mlflow.pyfunc
from botocore.exceptions import EndpointConnectionError
from dotenv import load_dotenv
from fastapi import HTTPException
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException
from mlflow.pyfunc import PyFuncModel


# 1. Définir la structure du dictionnaire
class State(TypedDict):
    model: Optional[PyFuncModel]
    version: Optional[str]


load_dotenv()
MODEL_NAME = "model_name"
MODEL_ALIAS = "Production"


MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5000")
MLFLOW_URI = f"http://mlflow:{MLFLOW_PORT}"

# Initialisation du client MLflow
client = MlflowClient(tracking_uri=MLFLOW_URI)

# Cache pour éviter de recharger le modèle si la version n'a pas changé
state: State = {"model": None, "version": None}


def load_production_model():
    """Vérifie la version en production et recharge si nécessaire."""
    try:
        # On demande au Registry quelle est la version actuelle de l'alias 'Production'
        alias_info = client.get_model_version_by_alias(MODEL_NAME, MODEL_ALIAS)
        prod_version = alias_info.version

        # Si le modèle n'est pas en cache oud si la version a changé sur MLflow
        if state["model"] is None or prod_version != state["version"]:
            print(f"Chargement de la version {prod_version} depuis MinIO...")
            model_uri = f"models:/{MODEL_NAME}@{MODEL_ALIAS}"
            model = mlflow.pyfunc.load_model(model_uri)
            if model is not None:
                state["model"] = model
                state["version"] = prod_version

        return state["model"], state["version"]
    except (EndpointConnectionError, MlflowException) as e:
        # Si MinIO ne répond pas, on garde l'ancien modèle en cache s'il existe
        if state["model"] is not None:
            print(
                f"⚠️ Erreur de connexion (MinIO/MLflow), on garde la version {state['version']} en cache."
            )
            return state["model"], state["version"]

        # Sinon, on lève une erreur explicite
        raise HTTPException(
            status_code=503,
            detail=f"Le service de stockage (MinIO) est indisponible : {str(e)}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
