import os

# GCP Configuration

GCP_PROJECT_ID = "amex-profitability-pipeline"
GCS_BUCKET_NAME = "amex-pipeline-nikhil-2026"
BQ_DATASET_ID = "amex_profitability"
BQ_TABLE_ID = "cleaned_transactions"
BQ_LOCATION = "asia-south1"


# Project Paths
THIS_DIR = os.path.dirname(os.path.abspath(__file__)) #where config.py is located
PROJECT_ROOT = os.path.dirname(THIS_DIR)

# service Account Key
CREDENTIALS_PATH = os.path.join(THIS_DIR, "gcp_credentials.json")

# Local Data
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "raw_data.csv")

# Save cleaned parquet inside data/processed/
CLEANED_DATA_PATH = os.path.join(
    PROJECT_ROOT,
    "data",
    "processed",
    "cleaned_data.parquet"
)

#Object Names

GCS_RAW_BLOB_NAME = "raw/raw_data.csv"
GCS_CLEANED_BLOB_NAME = "processed/cleaned_data.parquet"

#BQ

BQ_FULL_TABLE_ID = (
    f"{GCP_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"
)

#Auth

def set_credentials_env():
    """Point google-cloud libraries to the service account key."""
    if os.path.exists(CREDENTIALS_PATH):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
    else:
        raise FileNotFoundError(
            f"Service account key not found:\n{CREDENTIALS_PATH}"
        )