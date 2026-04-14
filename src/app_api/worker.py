import os
import time

import pandas as pd
from celery import Celery
from modules.load_model import load_production_model  # À adapter selon ton chemin

# Lecture des variables d'environnement (définies dans ton docker-compose)
BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
MODEL_LATENCY = int(os.getenv("MODEL_LATENCY", "0"))

app = Celery("prediction_worker", broker=BROKER_URL, backend=RESULT_BACKEND)


@app.task(name="predict_iris_task")
def predict_iris_task(data_dict: dict):
    """
    Tâche Celery pour effectuer la prédiction de manière asynchrone.
    """
    # 1. Simuler la latence si nécessaire (pour tester l'asynchrone)
    if MODEL_LATENCY > 0:
        time.sleep(MODEL_LATENCY)

    # 2. Charger le modèle
    model, version = load_production_model()
    if model is None:
        return {"error": "Modèle introuvable ou MLflow injoignable"}

    # 3. Préparer le DataFrame
    input_df = pd.DataFrame(
        [list(data_dict.values())],
        columns=[
            "sepal length (cm)",
            "sepal width (cm)",
            "petal length (cm)",
            "petal width (cm)",
        ],
    )

    # 4. Prédiction
    prediction = model.predict(input_df)
    target_names = ["setosa", "versicolor", "virginica"]
    predicted_class = target_names[int(prediction[0])]

    return {
        "prediction": predicted_class,
        "class_index": int(prediction[0]),
        "model_version": version,
    }
