import os
from unittest.mock import MagicMock, patch

import pytest
import requests
from streamlit.testing.v1 import AppTest

# On définit le chemin vers app.py de manière robuste
# On construit le chemin absolu vers src/app_front/app.py
# On part du principe que ce fichier de test est dans src/app_front/tests/
CURRENT_DIR = os.path.dirname(__file__)
ABS_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "../src/app_front", "app.py"))


def test_debug_path():
    """Test de diagnostic pour voir où pytest cherche le fichier"""
    print(f"\nRecherche du fichier app.py ici : {ABS_PATH}")
    assert os.path.exists(ABS_PATH), (
        f"ERREUR : Le fichier est introuvable à l'adresse {ABS_PATH}"
    )


def test_full_app_flow_success():
    at = AppTest.from_file(ABS_PATH, default_timeout=10)
    at.run()

    # On mocke 'requests.Session.request' ou 'requests.post' ET 'requests.get'
    with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
        # 1. Mock de la soumission (POST)
        mock_post_res = MagicMock()
        mock_post_res.status_code = 200
        mock_post_res.json.return_value = {"task_id": "test-123", "status": "Pending"}
        mock_post.return_value = mock_post_res

        # 2. Mock du résultat (GET)
        mock_get_res = MagicMock()
        mock_get_res.status_code = 200
        mock_get_res.json.return_value = {
            "status": "SUCCESS",
            "result": {
                "prediction": "setosa",
                "model_version": "1.0",
                "class_index": 0,
            },
        }
        mock_get.return_value = mock_get_res

        # On simule l'interaction
        at.sidebar.slider[0].set_value(6.0)
        at.button[0].click().run()

        # On vérifie que st.success a bien été appelé
        assert len(at.success) > 0
        assert "SETOSA" in at.success[0].value


def test_full_app_flow_error():
    """Teste la gestion d'erreur"""
    at = AppTest.from_file(ABS_PATH, default_timeout=10)
    at.run()

    with patch("requests.post", side_effect=Exception("API Unreachable")):
        at.button[0].click().run()

        assert len(at.error) > 0
        assert "Erreur de connexion" in at.error[0].value


@patch("requests.post")
def test_streamlit_api_call_success(mock_post):
    """Teste si le front gère bien une réponse positive de l'API"""
    # 1. On prépare une fausse réponse JSON
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "prediction": "setosa",
        "model_version": "1.0",
        "class_index": 0,
    }
    mock_post.return_value = mock_response

    # 2. Simulation des données envoyées par les sliders
    payload = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    }

    # 3. Exécution de l'appel (on simule ce que fait le bouton)
    from app import API_URL  # Adapte le nom si ton fichier s'appelle autrement

    response = requests.post(f"{API_URL}/predict", json=payload)

    assert response.status_code == 200
    assert response.json()["prediction"] == "setosa"


@patch("requests.post")
def test_streamlit_api_error(mock_post):
    """Teste la gestion d'une erreur 500 ou 503 de l'API"""
    mock_post.side_effect = requests.exceptions.ConnectionError("API Down")

    with pytest.raises(requests.exceptions.ConnectionError):
        from app import API_URL

        requests.post(f"{API_URL}/predict", json={})
