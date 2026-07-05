#ETL for amex 

import os
import sys
import pandas as pd
import numpy as np
from google.cloud import storage, bigquery

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

#extract

def extract(raw_path: str) -> pd.DataFrame:
    print(f"[EXTRACT] Reading raw data from {raw_path} ...")
    df = pd.read_csv(raw_path)
    print(f"[EXTRACT] Loaded {len(df):,} rows, {len(df.columns)} columns")
    return df


# transform

def clean_and_transform(df: pd.DataFrame) -> pd.DataFrame:

    # benefit / usage / count features: NaN = not used hence 0 ke equate kardo
    benefit_zero_fill = ['f13', 'f14', 'f15', 'f16', 'f19', 'f20', 'f21', 'f22', 'f23']
    for col in benefit_zero_fill:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # spend features: NaN = missing category spend (samae logic)
    spend_zero_fill = ['f5', 'f6', 'f7', 'f8', 'f9', 'f10']
    for col in spend_zero_fill:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # risk / revolve features: NaN = not a revolver (same logic)
    for col in ['f1', 'f2', 'f3', 'f11']:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # credit line features: median fill (if credit = NaN, matlab )
    for col in ['f17', 'f18']:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    # login counts: median fill
    if 'f12' in df.columns:
        df['f12'] = df['f12'].fillna(df['f12'].median())

    # rewards balance: zero fill
    if 'f4' in df.columns:
        df['f4'] = df['f4'].fillna(0)

    df.fillna(0, inplace=True)

    print("[TRANSFORM] Fixing f5 anomaly — reconstructing true total spend")
    # f5 does not represent true total spend (flaw in the data given)
    # f5 mean =3,465 vs f7 alone=30,822). True spend = sum of sub categories.
    df['true_total_spend'] = df['f6'] + df['f7'] + df['f8'] + df['f9'] + df['f10']
    df['f5_anomaly_flag'] = (df['f5'] < df['true_total_spend'] * 0.5).astype(int)

    print("[TRANSFORM] Adding derived features for downstream SQL/ML use")

    # credit utilization ratio
    if 'f17' in df.columns and 'f18' in df.columns:
        df['credit_utilization'] = np.clip(
            df['f18'] / df['f17'].replace(0, np.nan), 0, 1.0
        ).fillna(0)
    else:
        df['credit_utilization'] = 0.0

    # engagement score
    if 'f12' in df.columns and 'f22' in df.columns:
        norm_logins = np.clip(df['f12'] / 60, 0, 1.0)
        norm_emails = np.clip(df['f22'] / 20, 0, 1.0)
        df['engagement_score'] = norm_logins * 0.6 + norm_emails * 0.4
    else:
        df['engagement_score'] = 0.0

    #revolver flag
    if 'f1' in df.columns:
        df['is_revolver'] = (df['f1'] > 0).astype(int)

    spend_cols = ['f6', 'f7', 'f8', 'f9', 'f10']
    spend_cols = [c for c in spend_cols if c in df.columns]
    safe_total = df['true_total_spend'].replace(0, np.nan)
    for c in spend_cols:
        df[f'{c}_pct_of_spend'] = (df[c] / safe_total).fillna(0)

    print(f"[TRANSFORM] Final shape: {df.shape}")
    return df


#load

def upload_to_gcs(df: pd.DataFrame):
    print(f"[LOAD] Writing cleaned data to local Parquet")
    os.makedirs(os.path.dirname(config.CLEANED_DATA_PATH), exist_ok=True)
    df.to_parquet(config.CLEANED_DATA_PATH, index=False)

    print(f"[LOAD] Uploading to gs://{config.GCS_BUCKET_NAME}/{config.GCS_CLEANED_BLOB_NAME} ...")
    client = storage.Client(project=config.GCP_PROJECT_ID)
    bucket = client.bucket(config.GCS_BUCKET_NAME)
    blob = bucket.blob(config.GCS_CLEANED_BLOB_NAME)
    blob.upload_from_filename(config.CLEANED_DATA_PATH)
    print("[LOAD] Upload to GCS complete.")



# load into BigQuery
def load_to_bigquery():
    print(f"[LOAD] Loading into BigQuery table {config.BQ_FULL_TABLE_ID}")
    client = bigquery.Client(project=config.GCP_PROJECT_ID)

    # Ensure dataset exists
    dataset_ref = bigquery.DatasetReference(config.GCP_PROJECT_ID, config.BQ_DATASET_ID)
    try:
        client.get_dataset(dataset_ref)
    except Exception:
        print(f"[LOAD] Dataset {config.BQ_DATASET_ID} not found — creating it ...")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = config.BQ_LOCATION
        client.create_dataset(dataset)

    gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{config.GCS_CLEANED_BLOB_NAME}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # prevented overwrite on rerun (agar old data + new_data required hota to WRITE_APPEND use hota)
    )

    load_job = client.load_table_from_uri(
        gcs_uri, config.BQ_FULL_TABLE_ID, job_config=job_config
    )
    load_job.result()  

    table = client.get_table(config.BQ_FULL_TABLE_ID)
    print(f"[LOAD] Loaded {table.num_rows:,} rows into {config.BQ_FULL_TABLE_ID}")



def main():
    config.set_credentials_env()

    df = extract(config.RAW_DATA_PATH)
    df = clean_and_transform(df)
    upload_to_gcs(df)
    load_to_bigquery()

    print("\n[PIPELINE COMPLETE]")
    print(f"  - Cleaned Parquet: {config.CLEANED_DATA_PATH}")
    print(f"  - GCS location: gs://{config.GCS_BUCKET_NAME}/{config.GCS_CLEANED_BLOB_NAME}")
    print(f"  - BigQuery table: {config.BQ_FULL_TABLE_ID}")
  


if __name__ == "__main__":
    main()
