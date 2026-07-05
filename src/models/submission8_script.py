import pandas as pd
import numpy as np

def generate_v8_f5_reconstruction(input_path, output_path):
    """
    AMEX Premier Card Profitability Scoring — V8 (The Breakthrough)
    
    Design philosophy (based on deep structural analysis of V1-V7):
    
    1. THE BIG FIX (Reconstruct f5): 
       Data shows f5 mean is ~3,465, but f7 (Other Spend) mean is ~30,822. 
       f5 is NOT the true total spend. We must calculate true spend as:
       f6 + f7 + f8 + f9 + f10.
       
    2. THE COEFFICIENT ROLLBACK:
       V7 regressed because we strayed from the V2 coefficients that yielded 0.536.
       We are reverting exactly to:
       - 0.02 Interchange
       - 0.20 Interest
       - 50,000 Collection penalty (f3)
       - 250 Retention penalty (f2)
       - 1.0x ECL (f1 * f11)
       
    3. THE LTV CONSTRAINT:
       Multiplying base profit by 1.15 flipped ranks across profitability tiers, 
       ruining the top-20% boundary. LTV will now only be a microscopic 
       *additive nudge* (max +$1.70) to act purely as a tie-breaker.
    """
    
    df = pd.read_csv(input_path)
    
    # Benefit / usage / count features: NaN = not used / 0
    benefit_zero_fill = ['f13', 'f14', 'f15', 'f16', 'f19', 'f20', 'f21', 'f22', 'f23']
    for col in benefit_zero_fill:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    # Spend features: NaN = missing category spend, fill 0
    spend_zero_fill = ['f5', 'f6', 'f7', 'f8', 'f9', 'f10']
    for col in spend_zero_fill:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    # Risk / revolve features: fill 0 (no revolve = not a revolver)
    for col in ['f1', 'f2', 'f3', 'f11']:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    # Lend line: fill with median
    for col in ['f17', 'f18']:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    
    # Login counts: fill with median
    for col in ['f12']:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
    
    # Rewards balance (f4): fill 0 
    if 'f4' in df.columns:
        df['f4'] = df['f4'].fillna(0)
        
   
    df.fillna(0, inplace=True)
    
    predictions = pd.DataFrame({'ID': df['id']})

    #rev
    # Calculate TRUE total spend by summing all individual spend categories.
    true_total_spend = df['f6'] + df['f7'] + df['f8'] + df['f9'] + df['f10']

    rev_interchange = true_total_spend * 0.02
    
    rev_interest = df['f1'] * 0.20
    
    rev_supplementary = df['f19'] * 175
    
    total_revenue = rev_interchange + rev_interest + rev_supplementary
    
#cost
    
    cost_rewards = df['f21'] * 0.010
    cost_lounge = df['f13'] * 35
    cost_cab = df['f15'] * 15
    cost_air = df['f14']
    cost_ent = df['f16']
    
    total_costs = cost_rewards + cost_lounge + cost_cab + cost_air + cost_ent
    
#risk
    
    # reverting to 1x ECL multiplier from V2
    expected_loss = df['f1'] * df['f11']
    
    # reverting to 50K penalty from V2 
    collection_penalty = df['f3'] * 50000
    
    # reverting to 250 penalty from V2
    retention_penalty = df['f2'] * 250
    
    total_risk = expected_loss + collection_penalty + retention_penalty
    
    #base profit
    
    base_profit = total_revenue - total_costs - total_risk
    
#ltv nudge instead of multiplier
    
    norm_logins = np.clip(df['f12'] / 60, 0, 1.20) # Max 1.2
    norm_emails = np.clip(df['f22'] / 20, 0, 0.50) # Max 0.5
    
    ltv_nudge = norm_logins + norm_emails 
    
    # additive nudge
    df['Profitability_Score'] = base_profit + ltv_nudge
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
            'f1, f2, f3, f6, f7, f8, f9, f10 (True Spend), f11, f12, f13, f14, f15, f16, f19, f21, f22.',
            'Profit = Base V2 Revenue (using f6+f7+f8+f9+f10 instead of f5) - V2 Costs - V2 Risk + LTV Additive Nudge',
            'Bypasses the corrupted f5 variable by reconstructing true total spend from sub-categories. Reverts all weights to the proven V2 peak (0.536).',
            'Excluded f5 entirely. Constrained LTV engagement to a flat additive tie-breaker rather than a rank-breaking multiplier.',
            'Interchange (2.0%), Interest (20%), ECL (1.0x), Collection Penalty (50k), Retention (250). LTV capped at +$1.70 absolute value.',
            'Created true_total_spend feature. Converted multiplicative engagement into an additive scalar to prevent profit tier flipping.',
            'True total spend drives the majority of actual interchange value. f5 significantly underrepresented the portfolio volume based on data means.',
            'Assumed f6 through f10 exhaustively represent all charge volume. Assumed LTV should only influence micro-ranking (tie-breaking) rather than macro profitability.',
            'Addressing the V7 regression directly by anchoring to V2 weights and fixing the f5 anomaly identified in data profiling.',
            'V8 Submission - True Spend Reconstruction and V2 Calibration.'
        ]
    }
    framework_df = pd.DataFrame(framework_data)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        predictions.to_excel(writer, sheet_name='Predictions', index=False)
        framework_df.to_excel(writer, sheet_name='Profitability Framework', index=False)
        
    print(f"V8 Submission successfully generated and saved to: {output_path}")

if __name__ == "__main__":
    input_file = r"D:\cv_projects_2\amex_campus_challenge\data\raw\raw_data.csv"
    output_file = r"D:\cv_projects_2\amex_campus_challenge\submissions\submission8.xlsx"
    generate_v8_f5_reconstruction(input_file, output_file)