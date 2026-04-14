from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# 1. TEST : Route Racine
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "API is alive"}


# 2. TEST : Health Check
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


# 3. TEST : Metrics (Vérifie si Prometheus répond)
def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "system_cpu_usage" in response.text


# 4. TEST : Prédiction (Succès) — /predict retourne un task_id
@patch("main.predict_iris_task.delay")
def test_predict_success(mock_delay):
    mock_delay.return_value.id = "fake-task-id"

    payload = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    }
    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert response.json()["task_id"] == "fake-task-id"
    assert response.json()["status"] == "Pending"
    mock_delay.assert_called_once_with(payload)


# 5. TEST : Erreur broker — Celery indisponible
@patch("main.predict_iris_task.delay", side_effect=Exception("broker down"))
def test_predict_no_model(mock_delay):
    payload = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 500
    assert "broker" in response.json()["detail"]


# 6. TEST : /result — tâche en succès
@patch("main.AsyncResult")
def test_get_result_success(mock_async_result):
    mock_result = MagicMock()
    mock_result.status = "SUCCESS"
    mock_result.ready.return_value = True
    mock_result.successful.return_value = True
    mock_result.result = {
        "prediction": "setosa",
        "class_index": 0,
        "model_version": "1.0",
    }
    mock_async_result.return_value = mock_result

    response = client.get("/result/fake-task-id")

    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    assert response.json()["result"]["prediction"] == "setosa"


# 7. TEST : /result — tâche en cours (PENDING)
@patch("main.AsyncResult")
def test_get_result_pending(mock_async_result):
    mock_result = MagicMock()
    mock_result.status = "PENDING"
    mock_result.ready.return_value = False
    mock_result.successful.return_value = False
    mock_async_result.return_value = mock_result

    response = client.get("/result/fake-task-id")

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"
    assert response.json()["result"] is None


# 8. TEST : /result — tâche en échec (FAILURE)
@patch("main.AsyncResult")
def test_predict_error_during_inference(mock_async_result):
    mock_result = MagicMock()
    mock_result.status = "FAILURE"
    mock_result.ready.return_value = True
    mock_result.successful.return_value = False
    mock_result.result = {"error": "modèle introuvable"}
    mock_async_result.return_value = mock_result

    response = client.get("/result/fake-task-id")

    assert response.status_code == 200
    assert response.json()["status"] == "FAILURE"


# 9. TEST : Middleware — gestion des erreurs
def test_middleware_error_handling():
    """Force une erreur pour couvrir la branche 'except' du middleware"""
    with patch(
        "main.logger.debug", side_effect=RuntimeError("Middleware Trigger Test")
    ):
        with pytest.raises(RuntimeError):
            client.get("/health")
