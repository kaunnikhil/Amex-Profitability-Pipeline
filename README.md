# AMEX Premier Card — Cloud-Native Profitability & Risk Intelligence Pipeline

> **Campus Challenge Result:** Spearman Rank Correlation **0.906** (top-20% classification) across 10 systematic submissions  
> **Stack:** Python · Google BigQuery · Google Cloud Storage · XGBoost · Tableau · Excel

---

## Overview

End-to-end data science project built on an AMEX Premier card portfolio (500K customers, 23 features). The work spans a scoring competition, a cloud data pipeline, SQL analytics, machine learning, and executive dashboards.

| Feature | Description |
|---|---|
| f1 | Average Revolve Balance in last 12m |
| f2 | Cancellation Calls in last 12m |
| f3 | Cancellation Calls due to Collection |
| f4 |	Rewards Points Balance |
| f5 |	Total Spend in last 12m |
| f6 |	Airlines Spend in 12m |
| f7 |	Other Spend in 12m |
| f8 |	Entertainment Spend in 12m |
| f9 |	Lodging Spend in 12m |
| f10 | Dining Spend in 12m |
| f11 | Average Risk Score in 12m |
| f12 | Login Counts to website |
| f13 | Lounge Access Count |
| f14 | Credits used in airlines |
| f15 | Cab benefits usage |
| f16 | Entertainment Credit Used Amount |
| f17 | Total Lend Line Amount |
| f18 | Total Consumer Lend Line Amount |
| f19 | Number of Supplementary Accounts |
| f20 | Count of Active Charge Cards |
| f21 | Rewards point redeemed in 12months |
| f22 | Emails Open in Last 6 months |
| f23 | Emails Clicked in Last 6 months |


**The central finding:** The dataset's reported total spend field (`f5`) understated true spend by **14x**. Reconstructing spend from sub-category fields (`f6–f10`) was the foundational fix that drove all subsequent improvements.

---

## Project Architecture

```
Raw CSV (500K rows)
      │
      ▼
[ETL]  Python pipeline ──► Google Cloud Storage (raw + cleaned Parquet)
                                    │
                                    ▼
                             Google BigQuery
                           (cleaned_transactions,
                            v_profitability_scored view,
                            ml_training_data,
                            ml_predictions)
                                    │
                    ┌───────────────┼────────────────┐
                    ▼                                 ▼
             [SQL] EDA queries                  [ML] XGBoost
             9 BigQuery queries                 Binary classifier
             Segment analysis                   Feature importance
             Risk matrix                        Predictions → BQ
                    │                                 │
                    └───────────────┬─────────────────┘
                                    ▼
                    [Dashboards] Tableau (live BQ) + Excel (what-if)
```

---

## Repository Structure

```
AMEX_CA/
├── data/
│   ├── raw/                        # Raw CSV 
│   └── processed/                  # Cleaned Parquet 
├── etl/
│   ├── config.py                   # GCP project/bucket/dataset config
│   └── etl_pipeline.py             # Extract → Clean → Load to GCS + BQ
├── sql/
│   └── eda_queries.sql             # 9 BigQuery EDA + scoring queries
├── ml/
│   ├── model.py                    # XGBoost training, evaluation, BQ export
│   ├── feature_importance.csv      # Feature importance scores (top 20 features)
│   └── plots/
│       ├── feature_importance.png  # Feature importance bar chart
│       └── model_evaluation.png   # ROC curve, confusion matrix, PR curve
├── dashboard/
│   ├── excel_dashboard.py          # Programmatic Excel dashboard (openpyxl)
│   └── AMEX_Dashboard.xlsx         # Output — scenario simulator
├── src/
│   ├── features/                   # Feature engineering modules
│   └── models/
│       ├── submission1_script.py   # baseline (0.817 score)
│       ├── submission2_script.py   
│       │   ...
│       └── submission10_script.py  # V10 — final submission (0.906 score)
├── notebooks/                      # Exploratory notebooks
├── requirements.txt
└── README.md 
```

> **Note:** `etl/gcp_credentials.json`, raw data files, and submission Excel outputs are gitignored.  
> Set up your own GCP service account key following the ETL setup instructions below.

---

## Cloud ETL

**What it does:** Reads raw CSV → applies smart imputation → reconstructs true spend → adds derived features → uploads to GCS as Parquet → loads into BigQuery.

**Key derived features added at ETL time:**

| Feature | Formula | Purpose |
|---|---|---|
| `true_total_spend` | f6+f7+f8+f9+f10 | Corrects the f5 anomaly |
| `credit_utilization` | f18/f17 capped at 1.0 | Credit risk signal |
| `engagement_score` | 0.6×norm_logins + 0.4×norm_emails | Composite engagement |
| `is_revolver` | f1 > 0 | Revolver vs transactor flag |
| `f5_anomaly_flag` | f5 < true_total_spend×0.5 | Data quality audit flag |

**Setup:**
```bash
pip install -r requirements.txt

# Add your GCP service account key
cp /path/to/your-key.json etl/gcp_credentials.json

# Edit etl/config.py — set GCP_PROJECT_ID, GCS_BUCKET_NAME, BQ_DATASET_ID

python etl/etl_pipeline.py
```

---

## SQL EDA in BigQuery

9 queries in `sql/eda_queries.sql` covering:

- **Portfolio overview** — row counts, flag rates, null validation post-ETL
- **Feature distribution profile** — APPROX_QUANTILES percentiles for all features
- **f5 anomaly proof** — SQL exhibit: mean f5 (~3,400) vs mean true_total_spend (~48,500)
- **Profitability scoring view** — V13 heuristic as a persistent BigQuery VIEW using PERCENT_RANK()
- **Segment comparison** — Top 20% vs Bottom 80% across all dimensions
- **Decile breakdown** — NTILE(10) Pareto analysis
- **Risk segmentation** — 4-quadrant matrix (revolving balance × default probability)
- **Engagement quartile analysis** — validates the engagement multiplier
- **ML training table export** — CTAS materialising the labelled dataset

---

## Machine Learning

**Model:** XGBoost binary classifier — predicts top-20% profitable customers (label from V13 heuristic)

```
ROC-AUC:  0.999
Task:     Binary classification (Top 20% = 1, Bottom 80% = 0)
Features: 31 (23 raw + 8 derived, f5 excluded)
Split:    80/20 stratified
Imbalance: scale_pos_weight = 4.0
```

**On the 0.999 AUC:** The model is reconstructing a deterministic formula, not predicting stochastic outcomes. Near-perfect separation is expected when labels come from a heuristic. The value is in the **feature importance output** — XGBoost independently ranks the same features that the final submission coefficient search identified, providing mathematical validation of the scoring model.

```bash
python ml/model.py
```

---

## Dashboards

**Tableau:** 5-page workbook connected live to BigQuery
- Executive KPI overview, Decile Pareto, Risk segmentation matrix, ML feature importance, Engagement & spend mix
- Two independent data sources: `v_profitability_scored` and `feature_importance.csv` 

**Excel:** Programmatic dashboard (`excel_dashboard.py`) with 5 sheets including a **what-if scenario simulator** — four business levers (annual fee, interchange rate, churn reduction, supplementary cards) wired to Excel formulas for real-time scenario modelling.

```bash
python dashboard/excel_dashboard.py
```

---

## Campus Challenge — Scoring Submission Summary

The campus challenge required ranking ~500K customers by profitability (evaluated by Spearman rank correlation against hidden ground truth). 10 submissions were made across versions V1–V10.

| Version | Score | Key Change |
|---|---|---|
| V8  | 0.817 | f5 fix — reconstruct true spend from f6–f10 |
| V10 | **0.906** | Interest rate 0.20 to 0.25, rollback to proven anchors |

**Key learnings from 10 submissions:**
- Spearman rank means proportional coefficient changes are rank-neutral only changes that re-order specific customers matter
- f21 (rewards points balance) was over-penalising the highest-spend customers - the biggest single lever
- f2 (retention flag) penalises high-value at-risk customers; nullifying it improved rank
- Interest income rate (f1 × 0.25) correctly upweights revolvers but is sensitive to right-skew in f1

---

## Profitability Heuristic — V10 Final Formula

```
Score = (true_total_spend × 0.02
       + f1 × 0.25
       + f19 × 175
       + f4 × 0.00075
       + f20 × 50
       + f23 × 75)
       × (1 + engagement_score × 0.08)
       − (f21 × 0.002 + f13 × 35 + f15 × 15 + f14)
       − (f1 × f11 + f3 × 50,000)
```

Components: interchange (2% of true spend) + interest income (25% of revolving balance) + supplementary card revenue + loyalty signal + engagement uplift − benefit costs − rewards liability − expected credit loss − collection penalty

---

## Requirements

```
pandas>=2.0.0
numpy>=1.24.0
google-cloud-storage>=2.10.0
google-cloud-bigquery>=3.11.0
pyarrow>=14.0.0
db-dtypes>=1.1.0
xgboost>=2.0.0
scikit-learn>=1.3.0
openpyxl>=3.1.0
matplotlib>=3.7.0
seaborn>=0.12.0
```

---

