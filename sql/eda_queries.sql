--EDA 

SELECT
    COUNT(*)                              AS total_customers,
    COUNT(DISTINCT id)                    AS unique_customers,
    ROUND(AVG(true_total_spend), 2)       AS avg_true_spend,
    ROUND(AVG(f1), 2)                     AS avg_revolving_balance,
    ROUND(AVG(credit_utilization), 4)     AS avg_utilization,
    ROUND(AVG(engagement_score), 4)       AS avg_engagement,
    COUNTIF(f3 = 1)                       AS collection_flagged_count,
    ROUND(COUNTIF(f3 = 1) / COUNT(*) * 100, 2) AS collection_pct,
    COUNTIF(f2 = 1)                       AS retention_flagged_count,
    ROUND(COUNTIF(f2 = 1) / COUNT(*) * 100, 2) AS retention_pct,
    COUNTIF(is_revolver = 1)              AS revolver_count,
    ROUND(COUNTIF(is_revolver = 1) / COUNT(*) * 100, 2) AS revolver_pct,
    COUNTIF(f5_anomaly_flag = 1)          AS f5_anomaly_count,
    ROUND(COUNTIF(f5_anomaly_flag = 1) / COUNT(*) * 100, 2) AS f5_anomaly_pct
FROM `amex-profitability-pipeline.amex_profitability.cleaned_transactions`;



-- Q2: FEATURE DISTRIBUTION PROFILE
-- Percentiles, mean, stddev for all spend and risk features


SELECT
    feature,
    ROUND(avg_val, 2)    AS mean,
    ROUND(stddev_val, 2) AS stddev,
    ROUND(p25, 2)        AS p25,
    ROUND(p50, 2)        AS median,
    ROUND(p75, 2)        AS p75,
    ROUND(p90, 2)        AS p90,
    ROUND(p99, 2)        AS p99,
    ROUND(max_val, 2)    AS max
FROM (
    SELECT 'f1 (Revolving Balance)' AS feature, AVG(f1) avg_val, STDDEV(f1) stddev_val,
        APPROX_QUANTILES(f1, 100)[OFFSET(25)] p25,
        APPROX_QUANTILES(f1, 100)[OFFSET(50)] p50,
        APPROX_QUANTILES(f1, 100)[OFFSET(75)] p75,
        APPROX_QUANTILES(f1, 100)[OFFSET(90)] p90,
        APPROX_QUANTILES(f1, 100)[OFFSET(99)] p99,
        MAX(f1) max_val
    FROM `amex-profitability-pipeline.amex_profitability.cleaned_transactions`
    UNION ALL
    SELECT 'f4 (Rewards Balance)', AVG(f4), STDDEV(f4),
        APPROX_QUANTILES(f4, 100)[OFFSET(25)],
        APPROX_QUANTILES(f4, 100)[OFFSET(50)],
        APPROX_QUANTILES(f4, 100)[OFFSET(75)],
        APPROX_QUANTILES(f4, 100)[OFFSET(90)],
        APPROX_QUANTILES(f4, 100)[OFFSET(99)],
        MAX(f4)
    FROM `amex-profitability-pipeline.amex_profitability.cleaned_transactions`
    UNION ALL
    SELECT 'f5 (Reported Total - Anomalous)', AVG(f5), STDDEV(f5),
        APPROX_QUANTILES(f5, 100)[OFFSET(25)],
        APPROX_QUANTILES(f5, 100)[OFFSET(50)],
        APPROX_QUANTILES(f5, 100)[OFFSET(75)],
        APPROX_QUANTILES(f5, 100)[OFFSET(90)],
        APPROX_QUANTILES(f5, 100)[OFFSET(99)],
        MAX(f5)
    FROM `amex-profitability-pipeline.amex_profitability.cleaned_transactions`
    UNION ALL
    SELECT 'true_total_spend (f6+f7+f8+f9+f10)', AVG(true_total_spend), STDDEV(true_total_spend),
        APPROX_QUANTILES(true_total_spend, 100)[OFFSET(25)],
        APPROX_QUANTILES(true_total_spend, 100)[OFFSET(50)],
        APPROX_QUANTILES(true_total_spend, 100)[OFFSET(75)],
        APPROX_QUANTILES(true_total_spend, 100)[OFFSET(90)],
        APPROX_QUANTILES(true_total_spend, 100)[OFFSET(99)],
        MAX(true_total_spend)
    FROM `amex-profitability-pipeline.amex_profitability.cleaned_transactions`
    UNION ALL
    SELECT 'f6 (Spend Category 1)', AVG(f6), STDDEV(f6),
        APPROX_QUANTILES(f6, 100)[OFFSET(25)],
        APPROX_QUANTILES(f6, 100)[OFFSET(50)],
        APPROX_QUANTILES(f6, 100)[OFFSET(75)],
        APPROX_QUANTILES(f6, 100)[OFFSET(90)],
        APPROX_QUANTILES(f6, 100)[OFFSET(99)],
        MAX(f6)
    FROM `amex-profitability-pipeline.amex_profitability.cleaned_transactions`
    UNION ALL
    SELECT 'f7 (Spend Category 2 - Largest)', AVG(f7), STDDEV(f7),
        APPROX_QUANTILES(f7, 100)[OFFSET(25)],
        APPROX_QUANTILES(f7, 100)[OFFSET(50)],
        APPROX_QUANTILES(f7, 100)[OFFSET(75)],
        APPROX_QUANTILES(f7, 100)[OFFSET(90)],
        APPROX_QUANTILES(f7, 100)[OFFSET(99)],
        MAX(f7)
    FROM `amex-profitability-pipeline.amex_profitability.cleaned_transactions`
    UNION ALL
    SELECT 'f11 (Default Probability)', AVG(f11), STDDEV(f11),
        APPROX_QUANTILES(f11, 100)[OFFSET(25)],
        APPROX_QUANTILES(f11, 100)[OFFSET(50)],
        APPROX_QUANTILES(f11, 100)[OFFSET(75)],
        APPROX_QUANTILES(f11, 100)[OFFSET(90)],
        APPROX_QUANTILES(f11, 100)[OFFSET(99)],
        MAX(f11)
    FROM `amex-profitability-pipeline.amex_profitability.cleaned_transactions`
    UNION ALL
    SELECT 'f21 (Rewards Points Balance)', AVG(f21), STDDEV(f21),
        APPROX_QUANTILES(f21, 100)[OFFSET(25)],
        APPROX_QUANTILES(f21, 100)[OFFSET(50)],
        APPROX_QUANTILES(f21, 100)[OFFSET(75)],
        APPROX_QUANTILES(f21, 100)[OFFSET(90)],
        APPROX_QUANTILES(f21, 100)[OFFSET(99)],
        MAX(f21)
    FROM `amex-profitability-pipeline.amex_profitability.cleaned_transactions`
)
ORDER BY feature;



-- Q3: f5 ANOMALY CONFIRMATION
-- SQL proof that f5 underrepresents true spend
-- This is a key insight you can cite in interviews


SELECT
    'f5 (reported)'           AS metric,
    ROUND(AVG(f5), 2)         AS mean,
    ROUND(STDDEV(f5), 2)      AS stddev,
    ROUND(MAX(f5), 2)         AS max_value
FROM `mex-profitability-pipeline.amex_profitability.cleaned_transactions`
UNION ALL
SELECT
    'true_total_spend (f6–f10)',
    ROUND(AVG(true_total_spend), 2),
    ROUND(STDDEV(true_total_spend), 2),
    ROUND(MAX(true_total_spend), 2)
FROM `mex-profitability-pipeline.amex_profitability.cleaned_transactions`
UNION ALL
SELECT
    'underreporting gap (true - f5)',
    ROUND(AVG(true_total_spend - f5), 2),
    ROUND(STDDEV(true_total_spend - f5), 2),
    ROUND(MAX(true_total_spend - f5), 2)
FROM `mex-profitability-pipeline.amex_profitability.cleaned_transactions`
UNION ALL
SELECT
    '% customers where f5 < 50% of true spend',
    ROUND(COUNTIF(f5_anomaly_flag = 1) / COUNT(*) * 100, 2),
    NULL,
    NULL
FROM `mex-profitability-pipeline.amex_profitability.cleaned_transactions`;



-- Q4: APPLY V13 PROFITABILITY HEURISTIC + SEGMENT CUSTOMERS

CREATE OR REPLACE VIEW `amex-profitability-pipeline.amex_profitability.v_profitability_scored` AS
WITH scored AS (
    SELECT
        *,
        -- Rev
        (true_total_spend * 0.02)
        + (f1 * 0.25)
        + (f19 * 175)
        + (f4 * 0.00075)
        + (f20 * 50)
        + (f23 * 75)                                           AS total_revenue_pre_engagement,

        -- Engagement multiplier (8% max on revenue)
        (0.6 * LEAST(f12 / 60, 1.0) + 0.4 * LEAST(f22 / 20, 1.0))
                                                               AS engagement_score_raw,

        -- Costs
        (f21 * 0.002) + (f13 * 35) + (f15 * 15) + f14        AS total_costs,

        -- Risk
        (f1 * f11) + (f3 * 50000)                             AS total_risk

    FROM `amex-profitability-pipeline.amex_profitability.cleaned_transactions`
),
with_profit AS (
    SELECT
        *,
        total_revenue_pre_engagement * (1 + engagement_score_raw * 0.08)
            AS total_revenue,
        (total_revenue_pre_engagement * (1 + engagement_score_raw * 0.08))
            - total_costs
            - total_risk                                        AS profitability_score
    FROM scored
)
SELECT
    *,
    PERCENT_RANK() OVER (ORDER BY profitability_score DESC)    AS profitability_percentile,
    CASE
        WHEN PERCENT_RANK() OVER (ORDER BY profitability_score DESC) <= 0.20
        THEN 1 ELSE 0
    END                                                         AS is_top_20_pct
FROM with_profit;



-- Q5: TOP 20% vs BOTTOM 80% CUSTOMER PROFILE
-- answers the 'who are the most profitable customers'?


SELECT
    is_top_20_pct,
    COUNT(*)                                    AS customer_count,
    ROUND(AVG(profitability_score), 2)          AS avg_profit_score,
    ROUND(AVG(true_total_spend), 2)             AS avg_total_spend,
    ROUND(AVG(f1), 2)                           AS avg_revolving_balance,
    ROUND(AVG(f4), 2)                           AS avg_rewards_balance,
    ROUND(AVG(f11), 4)                          AS avg_default_prob,
    ROUND(AVG(f19), 2)                          AS avg_supplementary_cards,
    ROUND(AVG(f13), 2)                          AS avg_lounge_visits,
    ROUND(AVG(f21), 2)                          AS avg_rewards_points,
    ROUND(AVG(engagement_score), 4)             AS avg_engagement,
    ROUND(AVG(credit_utilization), 4)           AS avg_credit_utilization,
    ROUND(AVG(is_revolver), 4)                  AS pct_revolvers,
    COUNTIF(f3 = 1)                             AS collection_flagged,
    COUNTIF(f2 = 1)                             AS retention_flagged
FROM `amex-profitability-pipeline.amex_profitability.v_profitability_scored`
GROUP BY is_top_20_pct
ORDER BY is_top_20_pct DESC;



-- Q6: SPEND CATEGORY ANALYSIS
-- Which spend mix characterizes the most profitable customers?


SELECT
    is_top_20_pct,
    ROUND(AVG(f6), 2)                   AS avg_spend_cat1_f6,
    ROUND(AVG(f7), 2)                   AS avg_spend_cat2_f7,
    ROUND(AVG(f8), 2)                   AS avg_spend_cat3_f8,
    ROUND(AVG(f9), 2)                   AS avg_spend_cat4_f9,
    ROUND(AVG(f10), 2)                  AS avg_spend_cat5_f10,
    ROUND(AVG(f6_pct_of_spend), 4)      AS avg_f6_share,
    ROUND(AVG(f7_pct_of_spend), 4)      AS avg_f7_share,
    ROUND(AVG(f8_pct_of_spend), 4)      AS avg_f8_share,
    ROUND(AVG(f9_pct_of_spend), 4)      AS avg_f9_share,
    ROUND(AVG(f10_pct_of_spend), 4)     AS avg_f10_share
FROM `amex-profitability-pipeline.amex_profitability.v_profitability_scored`
GROUP BY is_top_20_pct
ORDER BY is_top_20_pct DESC;



-- Q7: PROFITABILITY DECILE BREAKDOWN

SELECT
    profitability_decile,
    COUNT(*)                                AS customers_in_decile,
    ROUND(MIN(profitability_score), 2)      AS min_score,
    ROUND(MAX(profitability_score), 2)      AS max_score,
    ROUND(AVG(profitability_score), 2)      AS avg_score,
    ROUND(AVG(true_total_spend), 2)         AS avg_spend,
    ROUND(AVG(f1), 2)                       AS avg_revolving_balance,
    ROUND(AVG(f11), 4)                      AS avg_default_prob,
    ROUND(SUM(profitability_score), 2)      AS total_segment_value
FROM (
    SELECT
        *,
        NTILE(10) OVER (ORDER BY profitability_score DESC) AS profitability_decile
    FROM `amex-profitability-pipeline.amex_profitability.v_profitability_scored`
)
GROUP BY profitability_decile
ORDER BY profitability_decile;



-- Q8: RISK SEGMENTATION — High Spend vs High Risk
-- Identifies the "risky revolvers" - high interest income but high ECL
-- These are the customers the ECL multiplier in V13 most affected


SELECT
    CASE
        WHEN f1 > 5000 AND f11 > 0.10  THEN 'High Balance + High Default Risk'
        WHEN f1 > 5000 AND f11 <= 0.10 THEN 'High Balance + Low Default Risk'
        WHEN f1 <= 5000 AND f11 > 0.10 THEN 'Low Balance + High Default Risk'
        ELSE                                 'Low Balance + Low Default Risk'
    END                                         AS risk_segment,
    COUNT(*)                                    AS customer_count,
    ROUND(AVG(profitability_score), 2)          AS avg_profit_score,
    ROUND(AVG(f1 * 0.25), 2)                   AS avg_interest_revenue,
    ROUND(AVG(f1 * f11), 2)                    AS avg_ecl,
    ROUND(AVG(true_total_spend * 0.02), 2)     AS avg_interchange_revenue,
    ROUND(COUNTIF(is_top_20_pct = 1) / COUNT(*) * 100, 2) AS pct_in_top_20
FROM `amex-profitability-pipeline.amex_profitability.v_profitability_scored`
GROUP BY risk_segment
ORDER BY avg_profit_score DESC;



-- Q9: ENGAGEMENT QUARTILE ANALYSIS
-- Does higher engagement = higher profitability?

SELECT
    engagement_quartile,
    COUNT(*)                                AS customers,
    ROUND(AVG(engagement_score), 4)         AS avg_engagement_score,
    ROUND(AVG(profitability_score), 2)      AS avg_profit_score,
    ROUND(AVG(true_total_spend), 2)         AS avg_spend,
    ROUND(COUNTIF(is_top_20_pct = 1) / COUNT(*) * 100, 2) AS pct_top_20
FROM (
    SELECT
        *,
        NTILE(4) OVER (ORDER BY engagement_score) AS engagement_quartile
    FROM `amex-profitability-pipeline.amex_profitability.v_profitability_scored`
)
GROUP BY engagement_quartile
ORDER BY engagement_quartile;



-- EXPORT: Save top 20% labelled dataset for ML 



CREATE OR REPLACE TABLE `amex-profitability-pipeline.amex_profitability.ml_training_data` AS
SELECT
    id,
    -- Feature set (all f1–f23 except f5, plus derived)
    f1, f2, f3, f4,
    f6, f7, f8, f9, f10,
    f11, f12, f13, f14, f15, f16,
    f17, f18, f19, f20, f21, f22, f23,
    true_total_spend,
    credit_utilization,
    engagement_score,
    is_revolver,
    f6_pct_of_spend,
    f7_pct_of_spend,
    f8_pct_of_spend,
    f9_pct_of_spend,
    f10_pct_of_spend,
    -- Label for ML
    is_top_20_pct                           AS label
FROM `amex-profitability-pipeline.amex_profitability.v_profitability_scored`;
