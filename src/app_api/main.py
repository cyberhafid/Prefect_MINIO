import os
import time

import psutil
import uvicorn
from celery.result import AsyncResult
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from loguru import logger
from modules.modele_reg import prepare_minio
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel
from starlette.responses import Response
from worker import predict_iris_task

load_dotenv()

app = FastAPI(title="Iris Prediction API")

# si problème dans les metrics de prometheus, on peut désenregistrer le registre
# for collector in list(REGISTRY._collector_to_names.keys()):
#     REGISTRY.unregister(collector)


# Monitoring
my_registry = CollectorRegistry()

REQUEST_COUNT = Counter(
    "app_requests_total",
    "Total des requêtes",
    ["method", "endpoint", "status_code"],
    registry=my_registry,
)

# 2. Durée des requêtes — permet P50/P90/P99
REQUEST_DURATION = Histogram(
    "app_request_duration_seconds",
    "Durée des requêtes en secondes",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
    registry=my_registry,
)

# 3. Requêtes en cours (en temps réel)
REQUESTS_IN_PROGRESS = Gauge(
    "app_requests_in_progress",
    "Requêtes en cours de traitement",
    registry=my_registry,
)

# 4. Prédictions par classe — détection de dérive du modèle
PREDICTION_COUNT = Counter(
    "app_predictions_total",
    "Prédictions par classe Iris",
    ["predicted_class"],
    registry=my_registry,
)

CPU_USAGE = Gauge("system_cpu_usage", "Usage CPU", registry=my_registry)

log_path = os.getenv(
    "LOG_PATH", "logs/fastapi.log"
)  # "logs/" sera dans le dossier courant
os.makedirs(os.path.dirname(log_path), exist_ok=True)
logger.add(log_path, rotation="500 MB")


# Middleware — instrumente toutes les routes
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    REQUESTS_IN_PROGRESS.inc()
    start = time.perf_counter()
    try:
        response = await call_next(request)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=str(response.status_code),
        ).inc()
        REQUEST_DURATION.labels(endpoint=request.url.path).observe(
            time.perf_counter() - start
        )
        return response
    except Exception as exc:
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code="500",
        ).inc()
        REQUEST_DURATION.labels(endpoint=request.url.path).observe(
            time.perf_counter() - start
        )
        raise exc
    finally:
        REQUESTS_IN_PROGRESS.dec()


# Définition du format d'entrée (les 4 mesures de la fleur)
class IrisInput(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float


@app.post("/predict")
async def predict(data: IrisInput):
    logger.info(f"Donnée reçue : {data}")
    try:
        task = predict_iris_task.delay(data.model_dump())
        return {"task_id": task.id, "status": "Pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur broker : {str(e)}")


@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """Récupère le résultat d'une tâche Celery par son ID."""
    result = AsyncResult(task_id)

    if result.ready() and result.successful():
        predicted_class = result.result.get("prediction")
        if predicted_class:
            # On incrémente le counter seulement quand le résultat est disponible
            PREDICTION_COUNT.labels(predicted_class=predicted_class).inc()

    return {
        "task_id": task_id,
        "status": result.status,  # PENDING | SUCCESS | FAILURE
        "result": result.result if result.ready() else None,
    }


# @app.post("/predict")
# async def predict(data: IrisInput):
#     # 1. Charger le modèle (utilise le cache ou recharge si nécessaire)
#     logger.info(f"Donnée reçue : {data}")
#     PREDICTION_COUNT.labels(predicted_class="test").inc()
#     # REQUEST_COUNT.labels(method="POST", endpoint="/predict").inc()
#     model, version = load_production_model()

#     if model is None:
#         raise HTTPException(status_code=500, detail="Le modèle n'a pas pu être chargé.")

#     # 2. Préparer les données pour le modèle (format DataFrame souvent requis par sklearn)
#     input_df = pd.DataFrame(
#         [data.model_dump().values()],
#         columns=[
#             "sepal length (cm)",
#             "sepal width (cm)",
#             "petal length (cm)",
#             "petal width (cm)",
#         ],
#     )

#     try:
#         # 3. Prédiction
#         prediction = model.predict(input_df)

#         # 4. Traduction du résultat (0, 1, 2) en nom de fleur
#         target_names = ["setosa", "versicolor", "virginica"]
#         predicted_class = target_names[int(prediction[0])]

#         PREDICTION_COUNT.labels(predicted_class=predicted_class).inc()

#         return {
#             "prediction": predicted_class,
#             "class_index": int(prediction[0]),
#             "model_version": version,
#         }
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"Erreur lors de la prédiction: {str(e)}"
#         )


@app.get("/")
async def root():
    # REQUEST_COUNT.labels(method="GET", endpoint="/").inc()
    return {"status": "API is alive"}


@app.get("/metrics")
async def metrics():
    CPU_USAGE.set(psutil.cpu_percent())
    return Response(generate_latest(my_registry), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health_check():
    logger.debug("get sur route health sonde uptime kuma")
    return {"status": "OK", "message": "API is running"}


if __name__ == "__main__":  # pragma: no cover
    prepare_minio()

    port_env = os.getenv("FASTAPI_PORT", "8000")
    host_url = "0.0.0.0"
    try:
        port = int(port_env)
    except (ValueError, TypeError):
        port = 8000
    uvicorn.run("main:app", host=host_url, port=port, log_level="debug")
