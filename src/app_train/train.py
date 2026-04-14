import os

import mlflow
import requests
from dotenv import load_dotenv
from mlflow.tracking import MlflowClient
from prefect import flow, task

load_dotenv()


# MLFLOW_HOST = os.getenv("MLFLOW_HOST", "127.0.0.1")
MLFLOW_HOST = os.getenv("MLFLOW_HOST_LOCAL", "127.0.0.1")
MLFLOW_PORT = os.getenv("MLFLOW_PORT", "5000")
TRACKING_URI = f"http://{MLFLOW_HOST}:{MLFLOW_PORT}"

# MINIO_HOST = os.getenv("MINIO_HOST", "127.0.0.1")
MINIO_HOST = os.getenv("MINIO_HOST_LOCAL", "127.0.0.1")
MINIO_PORT_S3 = os.getenv("MINIO_PORT_S3", "9000")
S3_ENDPOINT = f"http://{MINIO_HOST}:{MINIO_PORT_S3}"
os.environ["MLFLOW_TRACKING_URI"] = TRACKING_URI
os.environ["MLFLOW_S3_ENDPOINT_URL"] = S3_ENDPOINT
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
os.environ["AWS_ACCESS_KEY_ID"] = AWS_ACCESS_KEY_ID
os.environ["AWS_SECRET_ACCESS_KEY"] = AWS_SECRET_ACCESS_KEY


@task(name="Entrainement et enregistrement de model", retries=2)
def train_and_register(model, X_train, y_train, X_test, y_test, params):
    from mlflow import sklearn
    from services.def_model import model, params
    from sklearn.metrics import (
        accuracy_score,
    )

    # Configuration du serveur de tracking
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment("My_Experiment")
    # Chargement des données train/test

    with mlflow.start_run():
        # Entraînement
        model.fit(X_train, y_train)
        # Log des paramètres et metrics
        mlflow.log_params(params)
        y_pred = model.predict(X_test)

        # Evaluation du model
        accscore = accuracy_score(y_test, y_pred)
        metrics = {
            "accuracy": float(accscore),
        }
        mlflow.log_metrics(metrics)
        # 2. Enregistrement dans MinIO ET dans le Model Registry
        # On définit le nom du modèle dans le catalogue
        model_name = "model_name"
        sklearn.log_model(
            sk_model=model, artifact_path="model", registered_model_name=model_name
        )
    # 3. Gestion de l'Alias 'Production' via MlflowClient
    client = MlflowClient()

    # On récupère la toute dernière version créée
    latest_version = client.get_latest_versions(model_name, stages=["None"])[0].version

    # On lui attribue l'alias 'Production'
    client.set_registered_model_alias(model_name, "Production", latest_version)
    return model


@flow(name="Flow d'entrainement de model")
def flow_train():
    from services.def_model import model, params
    from services.prep_data_iris import prepare_data

    try:
        requests.get(TRACKING_URI)
        print(f"✅ Serveur MLflow accessible sur {TRACKING_URI} !")
    except Exception:
        print(f"❌ Erreur : Le serveur {TRACKING_URI} est injoignable.")
        exit(1)
    X_train, X_test, y_train, y_test = prepare_data()
    train_and_register(model, X_train, y_train, X_test, y_test, params)


if __name__ == "__main__":  # pragma: no cover
    import subprocess
    import sys

    from prefect.deployments import run_deployment

    if __name__ == "__main__":
        if len(sys.argv) > 1 and sys.argv[1] == "--run":
            run_deployment(name="Flow d'entrainement de model/train_a_model")
            print(" Run lancé !")
        elif len(sys.argv) > 1 and sys.argv[1] == "--init":
            print(" Mode init activé. Création du premier model...")
            flow_train()
        elif len(sys.argv) > 1 and sys.argv[1] == "--serve":
            print(" Mode .serve() activé. En attente de jobs...")
            flow_train.serve(
                name="train_a_model",
                cron="*/5 * * * *",
                tags=["local-serve"],
                description="Entraînement via méthode .serve()",
            )
        else:
            print(" Worker en attente...")
            subprocess.check_call(
                ["prefect", "worker", "start", "--pool", "train-pool"]
            )
