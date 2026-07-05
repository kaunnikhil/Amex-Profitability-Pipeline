import pandas as pd
import numpy as np
 
def generate_v9_submission(input_path, output_path):
    """
    AMEX Premier Card Profitability Scoring — V9 (Precision Calibration)
 
    Built on V8's 0.817 foundation. No structural overhaul — surgical tweaks only.
 
    CHANGES FROM V8:
    ─────────────────────────────────────────────────────────────
    1. DIFFERENTIATED INTERCHANGE RATES (biggest lever):
       V8 applied a flat 2% interchange across all spend categories.
       In reality, interchange varies by MCC category:
         - f6 (likely Travel/Airlines):    2.5% (premium MCC, high interchange)
         - f7 (likely Other/General):      2.0% (baseline, unchanged)
         - f8 (likely Dining/Restaurant):  2.3% (elevated MCC)
         - f9 (likely Utilities/Govt):     1.5% (low interchange category)
         - f10 (likely Retail/Shopping):   2.0% (baseline)
       This preserves the V2 anchor on total spend but distributes
       weights more precisely across categories.
 
    2. ENGAGEMENT MULTIPLIER ON REVENUE ONLY (not base_profit):
       V8's additive LTV nudge (+$1.70 max) was financially ungrounded.
       Engaged customers demonstrably spend more → we apply a small
       engagement uplift ONLY on the interchange revenue component.
       Max uplift: +3% on rev_interchange (e.g. a highly engaged customer
       generates slightly more spend-driven revenue). This is capped to
       prevent tier-crossing.
 
    3. REWARDS BALANCE (f4) AS LOYALTY SIGNAL:
       f4 was filled 0 and ignored in V8. High unredeemed rewards balance
       signals a loyal, high-spend customer unlikely to churn soon.
       Adding a tiny positive contribution: f4 * 0.0002 (micro-nudge).
 
    4. f23 UNLOCKED (small positive signal):
       f23 was zeroed and ignored. Adding f23 * 1.0 as a raw signal probe.
       If it carries no signal, its mean≈0 fill means it won't hurt rank.
 
    5. UTILIZATION PENALTY (f17/f18):
       f17/f18 are credit line features. High utilization relative to
       credit limit is a risk signal. We compute a soft utilization
       penalty using f18/f17 (capped at 1.0) and apply a small deduction.
       Customers near credit limit are riskier → small cost to their score.
 
    ANCHORS UNCHANGED FROM V8:
    - true_total_spend = f6+f7+f8+f9+f10 (f5 still excluded)
    - Interest: f1 * 0.20
    - ECL: f1 * f11 (1.0x multiplier)
    - Collection penalty: f3 * 50,000
    - Retention penalty: f2 * 250
    - Supplementary cards: f19 * 175
    - Core cost structure (lounge, cab, air, ent, rewards)
    """
 
    df = pd.read_csv(input_path)
 
    benefit_zero_fill = ['f13', 'f14', 'f15', 'f16', 'f19', 'f20', 'f21', 'f22', 'f23']
    for col in benefit_zero_fill:
        if col in df.columns:
            df[col] = df[col].fillna(0)
 
    spend_zero_fill = ['f5', 'f6', 'f7', 'f8', 'f9', 'f10']
    for col in spend_zero_fill:
        if col in df.columns:
            df[col] = df[col].fillna(0)
 
    for col in ['f1', 'f2', 'f3', 'f11']:
        if col in df.columns:
            df[col] = df[col].fillna(0)
 
    for col in ['f17', 'f18']:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
 
    for col in ['f12']:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
 
    if 'f4' in df.columns:
        df['f4'] = df['f4'].fillna(0)
 
    df.fillna(0, inplace=True)
 
    predictions = pd.DataFrame({'ID': df['id']})
 
  
 
    # Each spend category gets an MCC appropriate interchange rate
    # instead of V8's flat 2% across all categories.
    rev_interchange = (
        df['f6']  * 0.025 +   #premium MCC
        df['f7']  * 0.020 +   #baseline
        df['f8']  * 0.023 +   #Dining = elevated MCC
        df['f9']  * 0.015 +   #low MCC
        df['f10'] * 0.020     # e.g. Retail = baseline
    )
 
    # Interest income/unchanged from V2/V8
    rev_interest = df['f1'] * 0.20
 
    # Supplementary cards;unchanged from V2/V8
    rev_supplementary = df['f19'] * 175
 
    # Rewards balance loyalty signal (f4): high unredeemed balance = loyal customer
    # small nudge only = it won't meaningfully shift ranks but adds a truthful signal
    rev_loyalty = df['f4'] * 0.0002
 
    # f23 probe: previously zeroed feature
    rev_f23 = df['f23'] * 1.0
 
    total_revenue = rev_interchange + rev_interest + rev_supplementary + rev_loyalty + rev_f23
 


    cost_rewards  = df['f21'] * 0.010
    cost_lounge   = df['f13'] * 35
    cost_cab      = df['f15'] * 15
    cost_air      = df['f14']
    cost_ent      = df['f16']
 
    total_costs = cost_rewards + cost_lounge + cost_cab + cost_air + cost_ent
 
   
    expected_loss      = df['f1'] * df['f11']          # ECL: 1.0x multiplier
    collection_penalty = df['f3'] * 50000              # Binary flag × 50K
    retention_penalty  = df['f2'] * 250                # Retention risk flag × 250
 
    # Credit utilization soft penalty
    # High utilization (f18 balance / f17 credit limit) signals risk
    # capped at 1
    if 'f17' in df.columns and 'f18' in df.columns:
        utilization = np.clip(df['f18'] / df['f17'].replace(0, np.nan), 0, 1.0).fillna(0)
        # Penalty proportional to utilization above 80% threshold
        # Below 80%: no penalty (normal usage). Above 80%: soft cost signal.
        utilization_penalty = np.where(utilization > 0.80, (utilization - 0.80) * 500, 0)
    else:
        utilization_penalty = 0
 
    total_risk = expected_loss + collection_penalty + retention_penalty + utilization_penalty
 
    
    # BASE PROFIT
    
 
    base_profit = total_revenue - total_costs - total_risk
 
    
    # ENGAGEMENT UPLIFT — APPLIED TO INTERCHANGE ONLY
    # V8's additive nudge (+$1.70) was arbitrary. 
    # V9 grounds it: engaged customers generate more spend-driven revenue.
    # We scale rev_interchange upward by a small engagement factor.
    # Max engagement boost: +3% on interchange revenue.
    # This does NOT touch costs or risk, so it cannot flip profit tiers
    # for customers with large negative base_profits.
 
    norm_logins = np.clip(df['f12'] / 60, 0, 1.0)   # Normalized 0–1
    norm_emails = np.clip(df['f22'] / 20, 0, 1.0)   # Normalized 0–1
 
    # Composite engagement score (0 to 1)
    engagement_score = (norm_logins * 0.6 + norm_emails * 0.4)
 
    # Engagement uplift: max +3% of interchange revenue
    engagement_uplift = rev_interchange * engagement_score * 0.03
 
 
    df['Profitability_Score'] = base_profit + engagement_uplift
 
    predictions['Prediction'] = df['Profitability_Score']
 

    framework_data = {
        'Section': [
            'Variables Used',
            'Profitability Equation',
            'Prediction Logic',
            'Variable Selection Logic',
            'Coefficient/Weight Derivation',
            'Feature Transformations',
            'Business Logic',
            'Assumptions',
            'Validation Approach',
            'Additional Notes (Optional)'
        ],
        'Response': [
            'f1, f2, f3, f4, f6, f7, f8, f9, f10 (True Spend), f11, f12, f13, f14, f15, f16, f17, f18, f19, f21, f22, f23.',
            'Profit = Differentiated Interchange (by spend category) + Interest + Supplementary + Loyalty Signal + f23 - Costs - Risk - Utilization Penalty + Engagement Uplift on Interchange',
            'Preserves V8 true spend reconstruction. Differentiates interchange by MCC category. Applies engagement uplift only on revenue component to prevent profit-tier crossing. Unlocks f4 (loyalty) and f23 signals. Adds utilization-based risk penalty using f17/f18.',
            'f5 excluded (corrupted). f4 introduced as loyalty proxy. f23 introduced as signal probe. f17/f18 introduced for utilization risk. LTV applied as revenue-side multiplier, not additive profit nudge.',
            'Interchange: 2.5% Travel / 2.3% Dining / 2.0% General+Retail / 1.5% Utilities. Interest: 20%. ECL: 1.0x. Collection: 50K. Retention: 250. Engagement max uplift: 3% of interchange. Utilization penalty triggers above 80% utilization.',
            'true_total_spend still from f6–f10. Engagement score normalized 0–1 from f12 and f22. Utilization ratio from f18/f17 capped at 1.0 with penalty threshold at 0.80.',
            'Differentiated interchange reflects real MCC economics. Engagement uplift on revenue only preserves profit tier ordering. Utilization above 80% is a standard credit risk threshold. Rewards balance (f4) signals loyal high-spend customers unlikely to churn.',
            'Category assignments for f6–f10 are hypothesized from data means and AMEX product context. f23 signal direction assumed positive at 1.0x. Utilization penalty capped to avoid over-penalizing revolvers already penalized via ECL.',
            'Anchored to V8 structure (0.817 score). All changes are additive/marginal tweaks. Differentiated interchange is the primary experimental variable. Other changes act as tie-breakers.',
            'V9 Submission — Differentiated Interchange + Grounded Engagement Uplift + Feature Unlocks (f4, f23, f17/f18 utilization).'
        ]
    }
    framework_df = pd.DataFrame(framework_data)
 
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        predictions.to_excel(writer, sheet_name='Predictions', index=False)
        framework_df.to_excel(writer, sheet_name='Profitability Framework', index=False)
 
    print(f"V9 Submission successfully generated and saved to: {output_path}")
 
 
if __name__ == "__main__":
    input_file  = r"D:\cv_projects_2\amex_campus_challenge\data\raw\raw_data.csv"
    output_file = r"D:\cv_projects_2\amex_campus_challenge\submissions\submission9.xlsx"
    generate_v9_submission(input_file, output_file)