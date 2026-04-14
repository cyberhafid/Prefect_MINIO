from unittest.mock import patch

import pytest
from botocore.exceptions import EndpointConnectionError
from modules.modele_reg import prepare_minio


@pytest.fixture
def mock_s3():
    with patch("boto3.client") as mock_client:
        yield mock_client.return_value


# 1. TEST : BUCKET EXISTE DÉJÀ (Lignes 30-34)
def test_prepare_minio_bucket_exists(mock_s3):
    # On simule que le bucket 'mlflow' est déjà dans la liste
    mock_s3.list_buckets.return_value = {"Buckets": [{"Name": "mlflow"}]}

    with patch("time.sleep"):  # Pour ne pas ralentir le test
        prepare_minio()

    mock_s3.create_bucket.assert_not_called()


# 2. TEST : CRÉATION DU BUCKET (Ligne 34)
def test_prepare_minio_creates_bucket(mock_s3):
    # Liste vide au départ
    mock_s3.list_buckets.return_value = {"Buckets": []}

    prepare_minio()

    mock_s3.create_bucket.assert_called_once_with(Bucket="mlflow")


# 3. TEST : RÉSILIENCE ET ÉCHEC FINAL (Lignes 36-41)
def test_prepare_minio_retry_and_fail(mock_s3):
    # On simule une erreur de connexion systématique
    mock_s3.list_buckets.side_effect = EndpointConnectionError(endpoint_url="minio")

    with patch("time.sleep") as mock_sleep:
        prepare_minio()

        # On vérifie que le code a bien tenté 5 fois (le nombre de retries)
        assert mock_s3.list_buckets.call_count == 5
        assert mock_sleep.call_count == 5


# 4. TEST : SUCCÈS APRÈS UN ÉCHEC (Optionnel pour le 100% mais propre)
def test_prepare_minio_success_after_retry(mock_s3):
    # On échoue une fois, puis on réussit
    mock_s3.list_buckets.side_effect = [
        EndpointConnectionError(endpoint_url="minio"),
        {"Buckets": [{"Name": "mlflow"}]},
    ]

    with patch("time.sleep"):
        prepare_minio()

    assert mock_s3.list_buckets.call_count == 2
