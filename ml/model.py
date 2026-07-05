#AMEX card top 20% prob score 

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

from google.cloud import bigquery
import xgboost as xgb
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    classification_report, roc_auc_score, confusion_matrix,
    RocCurveDisplay, PrecisionRecallDisplay
)

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'etl'))
import config

config.set_credentials_env()


THIS_DIR  = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.join(THIS_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

FEATURE_COLS = [
    'f1', 'f2', 'f3', 'f4',
    'f6', 'f7', 'f8', 'f9', 'f10',
    'f11', 'f12', 'f13', 'f14', 'f15', 'f16',
    'f17', 'f18', 'f19', 'f20', 'f21', 'f22', 'f23',
    'true_total_spend',
    'credit_utilization',
    'engagement_score',
    'is_revolver',
    'f6_pct_of_spend', 'f7_pct_of_spend', 'f8_pct_of_spend',
    'f9_pct_of_spend', 'f10_pct_of_spend',
]
LABEL_COL = 'label'

FRIENDLY_NAMES = {
    'f1': 'Revolving Balance (f1)',
    'f2': 'Retention Flag (f2)',
    'f3': 'Collection Flag (f3)',
    'f4': 'Rewards Balance (f4)',
    'f6': 'Spend Cat 1 (f6)',
    'f7': 'Spend Cat 2 - Largest (f7)',
    'f8': 'Spend Cat 3 (f8)',
    'f9': 'Spend Cat 4 (f9)',
    'f10': 'Spend Cat 5 (f10)',
    'f11': 'Default Probability (f11)',
    'f12': 'Login Count (f12)',
    'f13': 'Lounge Visits (f13)',
    'f14': 'Air Benefit (f14)',
    'f15': 'Cab Trips (f15)',
    'f16': 'Ent Benefit (f16)',
    'f17': 'Credit Limit (f17)',
    'f18': 'Credit Balance (f18)',
    'f19': 'Supplementary Cards (f19)',
    'f20': 'Benefit Usage (f20)',
    'f21': 'Rewards Points (f21)',
    'f22': 'Email Engagement (f22)',
    'f23': 'Other Signal (f23)',
    'true_total_spend': 'True Total Spend',
    'credit_utilization': 'Credit Utilization Ratio',
    'engagement_score': 'Engagement Score',
    'is_revolver': 'Is Revolver Flag',
    'f6_pct_of_spend': 'f6 Share of Spend',
    'f7_pct_of_spend': 'f7 Share of Spend',
    'f8_pct_of_spend': 'f8 Share of Spend',
    'f9_pct_of_spend': 'f9 Share of Spend',
    'f10_pct_of_spend': 'f10 Share of Spend',
}


def load_from_bigquery() -> pd.DataFrame:
    print("[DATA] Pulling ml_training_data from BigQuery")
    client = bigquery.Client(project=config.GCP_PROJECT_ID) #for this we executed config.set_credentials_env() just adding an env var for the 'GOOGLE_APPLICATION_CREDENTIALS' 

    feature_list = ", ".join(FEATURE_COLS + [LABEL_COL])
    query = f"""
        SELECT {feature_list}
        FROM `{config.GCP_PROJECT_ID}.{config.BQ_DATASET_ID}.ml_training_data`
    """
    df = client.query(query).to_dataframe()
    print(f"[DATA] Loaded {len(df):,} rows. Label distribution:")
    print(df[LABEL_COL].value_counts(normalize=True).round(4).to_string())
    return df


# tt split
def split_data(df: pd.DataFrame):
    X = df[FEATURE_COLS]
    y = df[LABEL_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"[SPLIT] Train: {len(X_train):,} | Test: {len(X_test):,}")
    return X_train, X_test, y_train, y_test


#model train

def train_model(X_train, y_train) -> xgb.XGBClassifier:
    print("[TRAIN] training XGBoost")

    # scale_pos_weight handles class imbalance (80/20 split)
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos_weight = neg_count / pos_count
    print(f"[TRAIN] scale_pos_weight = {scale_pos_weight:.2f}")

    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        use_label_encoder=False,
        eval_metric='auc',
        early_stopping_rounds=30,
        random_state=1,
        n_jobs=-1,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train)],
        verbose=50,
    )

    print(f"[TRAIN] Best iteration: {model.best_iteration}")
    return model

#eval

def evaluate(model, X_test, y_test):
    print("\n[EVALUATE] Generating evaluation metrics")

    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    roc_auc = roc_auc_score(y_test, y_proba)
    print(f"\nROC-AUC Score: {roc_auc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Bottom 80%', 'Top 20%']))

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle('XGBoost Model Evaluation — AMEX Profitability Classifier', fontsize=14)

    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues', ax=axes[0],
        xticklabels=['Pred: Bottom 80%', 'Pred: Top 20%'],
        yticklabels=['True: Bottom 80%', 'True: Top 20%']
    )
    axes[0].set_title('Confusion Matrix')


    RocCurveDisplay.from_predictions(y_test, y_proba, ax=axes[1], name=f'XGBoost (AUC={roc_auc:.3f})')
    axes[1].plot([0, 1], [0, 1], 'k--', label='Random')
    axes[1].set_title('ROC Curve')
    axes[1].legend()

    PrecisionRecallDisplay.from_predictions(y_test, y_proba, ax=axes[2], name='XGBoost')
    axes[2].set_title('Precision-Recall Curve')

    plt.tight_layout()
    eval_path = os.path.join(PLOTS_DIR, 'model_evaluation.png')
    plt.savefig(eval_path, dpi=150, bbox_inches='tight')
    print(f"[EVALUATE] Saved evaluation plots → {eval_path}")
    plt.close()

    return roc_auc, y_proba


#feature importance

def plot_feature_importance(model, feature_cols: list):
    print("[IMPORTANCE] feature importance chart")

    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    importance_df['feature_label'] = importance_df['feature'].map(
        lambda x: FRIENDLY_NAMES.get(x, x)
    )

    top_n = importance_df.head(20)

    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(
        top_n['feature_label'][::-1],
        top_n['importance'][::-1],
        color='steelblue', edgecolor='white'
    )
    ax.bar_label(bars, fmt='%.4f', padding=3, fontsize=8)
    ax.set_xlabel('XGBoost Feature Importance (Gain)', fontsize=11)
    ax.set_title('Top 20 Features — XGBoost Rediscovery of Profitability Drivers\n'
                 '(Compare to V13 heuristic coefficients)', fontsize=12)
    ax.axvline(x=importance_df['importance'].mean(), color='red',
               linestyle='--', alpha=0.6, label='Mean importance')
    ax.legend()
    plt.tight_layout()

    importance_path = os.path.join(PLOTS_DIR, 'feature_importance.png')
    plt.savefig(importance_path, dpi=150, bbox_inches='tight')
    print(f"[IMPORTANCE] Saved feature importance chart → {importance_path}")
    plt.close()

    print("\nTop 10 features by importance:")
    print(importance_df[['feature_label', 'importance']].head(10).to_string(index=False))

    importance_csv = os.path.join(THIS_DIR, 'feature_importance.csv')
    importance_df.to_csv(importance_csv, index=False)
    print(f"[IMPORTANCE] Saved feature importance CSV → {importance_csv}")

    return importance_df



# SCORE FULL DATASET + EXPORT TO BIGQUERY


def export_predictions_to_bigquery(model, df: pd.DataFrame, roc_auc: float):
    print("\n[EXPORT] Scoring full dataset and exporting to BigQuery")

    client = bigquery.Client(project=config.GCP_PROJECT_ID)

    X_full = df[FEATURE_COLS]
    df = df.copy()
    df['ml_top20_probability'] = model.predict_proba(X_full)[:, 1]
    df['ml_predicted_top20']   = model.predict(X_full)

    # rank customers by ML probability
    df['ml_profitability_rank'] = df['ml_top20_probability'].rank(
        ascending=False, method='first'
    ).astype(int)

    export_cols = (
        FEATURE_COLS
        + [LABEL_COL, 'ml_top20_probability', 'ml_predicted_top20', 'ml_profitability_rank']
    )
    export_df = df[export_cols]

    dest_table = f"{config.GCP_PROJECT_ID}.{config.BQ_DATASET_ID}.ml_predictions"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    job = client.load_table_from_dataframe(export_df, dest_table, job_config=job_config)
    job.result()

    print(f"[EXPORT] {len(export_df):,} rows written to {dest_table}")
    print(f"[EXPORT] Model ROC-AUC: {roc_auc:.4f}")

    summary_df = pd.DataFrame([{
        'model_version': 'xgboost_v1',
        'roc_auc': round(roc_auc, 4),
        'n_estimators': model.best_iteration,
        'n_features': len(FEATURE_COLS),
        'train_size': 400000,
        'test_size': 100000,
        'label_positive_rate': 0.20,
        'notes': 'Labels from V13 heuristic (top 20% by profitability score)'
    }])
    summary_table = f"{config.GCP_PROJECT_ID}.{config.BQ_DATASET_ID}.ml_model_summary"
    job2 = client.load_table_from_dataframe(
        summary_df, summary_table,
        job_config=bigquery.LoadJobConfig(write_disposition='WRITE_TRUNCATE', autodetect=True)
    )
    job2.result()
    print(f"[EXPORT] Model summary written to {summary_table}")



def main():
    df = load_from_bigquery()

    X_train, X_test, y_train, y_test = split_data(df)

    model = train_model(X_train, y_train)

    roc_auc, y_proba = evaluate(model, X_test, y_test)

    importance_df = plot_feature_importance(model, FEATURE_COLS)

    export_predictions_to_bigquery(model, df, roc_auc)


    print(f"  ROC-AUC:            {roc_auc:.4f}")
    print(f"  Top feature:        {importance_df.iloc[0]['feature_label']}")
    print(f"  Plots saved to:     {PLOTS_DIR}/")
    print(f"  Predictions in BQ:  {config.GCP_PROJECT_ID}.{config.BQ_DATASET_ID}.ml_predictions")
   

if __name__ == "__main__":
    main()
