from unittest.mock import patch

import pytest
from botocore.exceptions import EndpointConnectionError
from fastapi import HTTPException

# --- IMPORT DES VRAIES EXCEPTIONS ---
from mlflow.exceptions import MlflowException
from modules.load_model import load_production_model


@pytest.fixture
def mock_state():
    """Reset du state global pour chaque test."""
    return {"model": None, "version": None}


@pytest.fixture
def mock_env_vars():
    """Mock du client MLflow."""
    with (
        patch("modules.load_model.client") as mock_client,
        patch("modules.load_model.MODEL_NAME", "test_model"),
        patch("modules.load_model.MODEL_ALIAS", "Production"),
    ):
        yield mock_client


# --- TESTS ---


def test_load_initial_success(mock_state, mock_env_vars):
    """Couvre : Premier chargement réussi"""
    # FIX: On force la version à être une string "1.0"
    mock_env_vars.get_model_version_by_alias.return_value.version = "1.0"

    with (
        patch("modules.load_model.state", mock_state),
        patch("mlflow.pyfunc.load_model", return_value="FakeModel"),
    ):
        model, version = load_production_model()
        assert version == "1.0"  # Maintenant c'est bien une string
        assert mock_state["model"] == "FakeModel"


def test_load_no_change(mock_state, mock_env_vars):
    """Couvre : Version identique (Branche IF sautée)"""
    # FIX: On aligne la version du mock avec celle du cache
    mock_state.update({"model": "Cached", "version": "1.0"})
    mock_env_vars.get_model_version_by_alias.return_value.version = "1.0"

    with (
        patch("modules.load_model.state", mock_state),
        patch("mlflow.pyfunc.load_model") as m_load,
    ):
        model, version = load_production_model()
        # Le cache doit fonctionner : load_model ne doit PAS être appelé
        m_load.assert_not_called()
        assert version == "1.0"
        assert model == "Cached"


def test_resilience_with_cache(mock_state, mock_env_vars):
    """Couvre : Erreur réseau avec cache (Lignes 58-63)"""
    mock_state.update({"model": "OldModel", "version": "v0"})
    mock_env_vars.get_model_version_by_alias.side_effect = MlflowException(
        "Connexion error"
    )
    with patch("modules.load_model.state", mock_state):
        model, version = load_production_model()
        assert model == "OldModel"


def test_error_503_no_cache(mock_state, mock_env_vars):
    """Couvre : Erreur réseau sans cache (Lignes 66-70)"""
    mock_env_vars.get_model_version_by_alias.side_effect = EndpointConnectionError(
        endpoint_url="minio"
    )
    with patch("modules.load_model.state", mock_state):
        with pytest.raises(HTTPException) as exc:
            load_production_model()
        assert exc.value.status_code == 503


def test_error_500_generic(mock_state, mock_env_vars):
    """Couvre : Erreur Exception finale (Lignes 71-72)"""
    mock_env_vars.get_model_version_by_alias.side_effect = ValueError("Boom")
    with patch("modules.load_model.state", mock_state):
        with pytest.raises(HTTPException) as exc:
            load_production_model()
        assert exc.value.status_code == 500
