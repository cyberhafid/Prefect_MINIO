import os
import time

import boto3
from botocore.exceptions import EndpointConnectionError
from dotenv import load_dotenv

load_dotenv()
MINIO_PORT_S3 = os.getenv("MINIO_PORT_S3", "9000")
MLFLOW_S3_ENDPOINT_URL = f"http://minio:{MINIO_PORT_S3}"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
REGION_NAME = os.getenv("REGION_NAME", "minioadmin")


def prepare_minio():
    """Vérifie si le bucket 'mlflow' existe, sinon le crée"""
    print("Vérification de MinIO...")
    s3 = boto3.client(
        "s3",
        endpoint_url=MLFLOW_S3_ENDPOINT_URL,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=REGION_NAME,
    )
    retries = 5
    while retries > 0:
        try:
            buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]

            if "mlflow" not in buckets:
                s3.create_bucket(Bucket="mlflow")
                print("Bucket 'mlflow' créé avec succès.")
            return
        except (EndpointConnectionError, Exception):
            print(f"MinIO n'est pas encore prêt... ({retries} tentatives restantes)")
            retries -= 1
            time.sleep(2)

    print("Impossible de se connecter à MinIO après plusieurs tentatives.")
