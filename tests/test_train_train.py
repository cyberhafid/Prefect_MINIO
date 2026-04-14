"""
test_train.py — 100 % coverage pour train.py

Stratégie :
  - Tous les modules externes (prefect, mlflow, requests, dotenv,
    sklearn, services) sont mockés dans sys.modules AVANT l'import
    de train, afin que le code exécuté au niveau du module se déroule
    proprement.
  - Les décorateurs @task/@flow sont remplacés par un passthrough
    (la fonction est renvoyée telle quelle) pour pouvoir tester les
    fonctions directement.
  - Le bloc `if __name__ == "__main__":` porte déjà `# pragma: no cover`
    et est donc exclu de la couverture.
"""

import os
import sys
from unittest.mock import MagicMock, patch

# ─────────────────────────────────────────────────────────────────────────────
# 1. Construction des mocks
# ─────────────────────────────────────────────────────────────────────────────


def _passthrough_decorator(*args, **kwargs):
    """Simule @task(…) / @flow(…) : renvoie la fonction enveloppée telle quelle."""

    def decorator(func):
        return func

    return decorator


# prefect ──────────────────────────────────────────────────────────────────────
_mock_prefect = MagicMock()
_mock_prefect.task = _passthrough_decorator
_mock_prefect.flow = _passthrough_decorator

# mlflow ───────────────────────────────────────────────────────────────────────
_mock_mlflow = MagicMock()
_mock_mlflow_tracking = MagicMock()

# requests / dotenv ────────────────────────────────────────────────────────────
_mock_requests = MagicMock()
_mock_dotenv = MagicMock()

# sklearn.metrics ──────────────────────────────────────────────────────────────
_mock_sklearn_metrics = MagicMock()
_mock_sklearn_metrics.accuracy_score = MagicMock(return_value=0.95)

# services.def_model ───────────────────────────────────────────────────────────
_mock_model = MagicMock(name="sklearn_model")
_mock_params = {"n_estimators": 100}
_mock_def_model = MagicMock()
_mock_def_model.model = _mock_model
_mock_def_model.params = _mock_params

# services.prep_data_iris ──────────────────────────────────────────────────────
_mock_prepare_data = MagicMock(return_value=([[1, 2], [3, 4]], [[5, 6]], [0, 1], [0]))
_mock_prep_data = MagicMock()
_mock_prep_data.prepare_data = _mock_prepare_data

# ─────────────────────────────────────────────────────────────────────────────
# 2. Installation des mocks dans sys.modules (avant tout import de train)
# ─────────────────────────────────────────────────────────────────────────────

sys.modules.update(
    {
        "prefect": _mock_prefect,
        "prefect.deployments": MagicMock(),
        "mlflow": _mock_mlflow,
        "mlflow.tracking": _mock_mlflow_tracking,
        "mlflow.sklearn": MagicMock(),
        "requests": _mock_requests,
        "dotenv": _mock_dotenv,
        "sklearn": MagicMock(),
        "sklearn.metrics": _mock_sklearn_metrics,
        "services": MagicMock(),
        "services.def_model": _mock_def_model,
        "services.prep_data_iris": _mock_prep_data,
    }
)

# Variables d'environnement requises par le code module-level de train.py
os.environ["MLFLOW_HOST_LOCAL"] = "mlflow-test-host"
os.environ["MLFLOW_PORT"] = "5001"
os.environ["MINIO_HOST_LOCAL"] = "minio-test-host"
os.environ["MINIO_PORT_S3"] = "9001"
os.environ["AWS_ACCESS_KEY_ID"] = "test-access-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test-secret-key"

import train  # noqa: E402  – importé après configuration des mocks

# ─────────────────────────────────────────────────────────────────────────────
# 3. Utilitaires
# ─────────────────────────────────────────────────────────────────────────────


def _make_client(version: str = "1") -> MagicMock:
    """Crée un mock MlflowClient dont get_latest_versions retourne *version*."""
    client = MagicMock()
    mv = MagicMock()
    mv.version = version
    client.get_latest_versions.return_value = [mv]
    _mock_mlflow_tracking.MlflowClient.return_value = client
    return client


# ─────────────────────────────────────────────────────────────────────────────
# 4. Tests des constantes module-level
# ─────────────────────────────────────────────────────────────────────────────


class TestModuleConstants:
    def test_tracking_uri_built_from_env(self):
        assert train.TRACKING_URI == "http://mlflow-test-host:5001"

    def test_s3_endpoint_built_from_env(self):
        assert train.S3_ENDPOINT == "http://minio-test-host:9001"

    def test_mlflow_tracking_uri_env_var_set(self):
        assert os.environ["MLFLOW_TRACKING_URI"] == "http://mlflow-test-host:5001"

    def test_mlflow_s3_endpoint_env_var_set(self):
        assert os.environ["MLFLOW_S3_ENDPOINT_URL"] == "http://minio-test-host:9001"

    def test_aws_access_key_env_var_set(self):
        assert os.environ["AWS_ACCESS_KEY_ID"] == "test-access-key"

    def test_aws_secret_key_env_var_set(self):
        assert os.environ["AWS_SECRET_ACCESS_KEY"] == "test-secret-key"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Tests de train_and_register
# ─────────────────────────────────────────────────────────────────────────────


class TestTrainAndRegister:
    """Tests unitaires de la tâche train_and_register."""

    # Données réutilisables ───────────────────────────────────────────────────
    X_TRAIN = [[1, 2], [3, 4]]
    X_TEST = [[5, 6]]
    Y_TRAIN = [0, 1]
    Y_TEST = [0]
    PARAMS = {"alpha": 0.1}

    def setup_method(self):
        _mock_mlflow.reset_mock()
        _mock_mlflow_tracking.reset_mock()
        _mock_model.reset_mock()
        _mock_sklearn_metrics.accuracy_score.reset_mock()
        _mock_sklearn_metrics.accuracy_score.return_value = 0.95

    def _call(self, version: str = "1"):
        """Appelle train_and_register avec un MlflowClient mocké."""
        client = _make_client(version)
        result = train.train_and_register(
            _mock_model,
            self.X_TRAIN,
            self.Y_TRAIN,
            self.X_TEST,
            self.Y_TEST,
            self.PARAMS,
        )
        return result, client

    # ── Valeur de retour ────────────────────────────────────────────────────

    def test_returns_model_from_services(self):
        """La fonction doit renvoyer le modèle importé depuis services.def_model."""
        result, _ = self._call()
        # À l'intérieur de la tâche, `from services.def_model import model`
        # écrase le paramètre → la valeur est _mock_def_model.model.
        assert result is _mock_def_model.model

    # ── Configuration MLflow ────────────────────────────────────────────────

    def test_sets_tracking_uri(self):
        self._call()
        _mock_mlflow.set_tracking_uri.assert_called_once_with(train.TRACKING_URI)

    def test_sets_experiment_name(self):
        self._call()
        _mock_mlflow.set_experiment.assert_called_once_with("My_Experiment")

    def test_start_run_is_called(self):
        self._call()
        _mock_mlflow.start_run.assert_called_once()

    # ── Entraînement et prédiction ──────────────────────────────────────────

    def test_fits_model_with_training_data(self):
        self._call()
        _mock_def_model.model.fit.assert_called_once_with(self.X_TRAIN, self.Y_TRAIN)

    def test_predicts_on_test_data(self):
        self._call()
        _mock_def_model.model.predict.assert_called_once_with(self.X_TEST)

    # ── Logging MLflow ──────────────────────────────────────────────────────

    def test_logs_params(self):
        self._call()
        _mock_mlflow.log_params.assert_called_once_with(_mock_def_model.params)

    def test_logs_accuracy_metric(self):
        _mock_sklearn_metrics.accuracy_score.return_value = 0.88
        self._call()
        _mock_mlflow.log_metrics.assert_called_once_with({"accuracy": 0.88})

    def test_accuracy_metric_is_cast_to_float(self):
        """float() doit être appliqué au score avant logging."""
        _mock_sklearn_metrics.accuracy_score.return_value = 1  # int
        self._call()
        logged = _mock_mlflow.log_metrics.call_args[0][0]
        assert isinstance(logged["accuracy"], float)

    def test_logs_model_to_registry(self):
        self._call()
        _mock_mlflow.sklearn.log_model.assert_called_once_with(
            sk_model=_mock_def_model.model,
            artifact_path="model",
            registered_model_name="model_name",
        )

    # ── Gestion de l'alias Production ───────────────────────────────────────

    def test_queries_latest_version_from_none_stage(self):
        _, client = self._call()
        client.get_latest_versions.assert_called_once_with(
            "model_name", stages=["None"]
        )

    def test_sets_production_alias_with_correct_version(self):
        _, client = self._call(version="42")
        client.set_registered_model_alias.assert_called_once_with(
            "model_name", "Production", "42"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 6. Tests de flow_train
# ─────────────────────────────────────────────────────────────────────────────


class TestFlowTrain:
    """Tests unitaires du flow flow_train."""

    def setup_method(self):
        _mock_requests.reset_mock()
        _mock_prepare_data.reset_mock()
        _mock_prepare_data.return_value = ([[1, 2]], [[3, 4]], [0], [0])

    # ── Chemin nominal (serveur accessible) ─────────────────────────────────

    def test_requests_get_called_with_tracking_uri(self):
        _mock_requests.get.return_value = MagicMock(status_code=200)
        with patch.object(train, "train_and_register"):
            train.flow_train()
        _mock_requests.get.assert_called_once_with(train.TRACKING_URI)

    def test_prepare_data_called_on_success(self):
        _mock_requests.get.return_value = MagicMock(status_code=200)
        with patch.object(train, "train_and_register"):
            train.flow_train()
        _mock_prepare_data.assert_called_once()

    def test_train_and_register_called_with_correct_args(self):
        _mock_requests.get.return_value = MagicMock(status_code=200)
        _mock_prepare_data.return_value = ([[1, 2]], [[5, 6]], [0], [1])

        with patch.object(train, "train_and_register") as mock_train:
            train.flow_train()

        # Ordre d'unpacking : X_train, X_test, y_train, y_test = prepare_data()
        # Appel : train_and_register(model, X_train, y_train, X_test, y_test, params)
        mock_train.assert_called_once_with(
            _mock_def_model.model,
            [[1, 2]],  # X_train
            [0],  # y_train
            [[5, 6]],  # X_test
            [1],  # y_test
            _mock_def_model.params,
        )

    def test_success_prints_accessible_message(self, capsys):
        _mock_requests.get.return_value = MagicMock(status_code=200)
        with patch.object(train, "train_and_register"):
            train.flow_train()
        captured = capsys.readouterr()
        assert "accessible" in captured.out

    # ── Chemin d'erreur (serveur injoignable) ───────────────────────────────

    def test_server_unreachable_calls_exit_1(self):
        _mock_requests.get.side_effect = Exception("Connection refused")
        with (
            patch("builtins.exit") as mock_exit,
            patch.object(train, "train_and_register"),
        ):
            train.flow_train()
        mock_exit.assert_called_once_with(1)

    def test_server_unreachable_prints_error_message(self, capsys):
        _mock_requests.get.side_effect = Exception("Timeout")
        with patch("builtins.exit"), patch.object(train, "train_and_register"):
            train.flow_train()
        captured = capsys.readouterr()
        assert "injoignable" in captured.out

    def test_any_exception_triggers_exit(self):
        """Toute exception (pas seulement ConnectionError) doit déclencher exit(1)."""
        _mock_requests.get.side_effect = RuntimeError("unexpected")
        with (
            patch("builtins.exit") as mock_exit,
            patch.object(train, "train_and_register"),
        ):
            train.flow_train()
        mock_exit.assert_called_once_with(1)
