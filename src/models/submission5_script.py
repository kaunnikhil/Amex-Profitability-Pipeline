import pandas as pd
import numpy as np

def generate_v5_comprehensive(input_path, output_path):
    print(f"Loading raw data for Comprehensive V5 from {input_path}...")
    df = pd.read_csv(input_path)
    
   
    df.fillna(0, inplace=True)
    predictions = pd.DataFrame({'ID': df['id']})
    
    # Rev
    # premium cards derive more value from spend (interchange) than interest.
    rev_interchange = df['f5'] * 0.025  # Boosted from 0.02
    rev_interest = df['f1'] * 0.15      # Reduced from 0.20
    rev_supplementary = df['f19'] * 175 
    
    # reintroduced the primary fee safely at the 500 minimum bound.
    rev_annual_fee = df['f20'] * 500    
    
    total_revenue = rev_interchange + rev_interest + rev_supplementary + rev_annual_fee
    
    # Cost
    cost_rewards = df['f21'] * 0.010 
    cost_lounge = df['f13'] * 35      
    cost_cab = df['f15'] * 15         
    cost_air = df['f14']              
    cost_ent = df['f16']              
    
    total_benefits = cost_rewards + cost_lounge + cost_cab + cost_air + cost_ent
    
    # risk
    # Premium portfolios severely punish ECL
    expected_loss = (df['f1'] * df['f11']) * 1.5 
    collection_penalty = df['f3'] * 50000 
    retention_penalty = df['f2'] * 250 
    
    # Calculate Base Historical Profit
    base_profit = total_revenue - total_benefits - expected_loss - collection_penalty - retention_penalty
    
    # Engagement LTV Multiplier 
    # f12 (Logins) and f22 (Email opens) used as proxies for retention & loyalty.
    # We clip to prevent extreme outliers from skewing the multiplier. Max total boost = 15%.
    norm_logins = np.clip(df['f12'] / 50, 0, 0.10) # 50 logins = max 10% boost
    norm_emails = np.clip(df['f22'] / 20, 0, 0.05) # 20 emails = max 5% boost
    
    ltv_multiplier = 1.0 + norm_logins + norm_emails
    
    # applying multiplier ONLY to mathematically profitable accounts
    df['Profitability_Score'] = np.where(base_profit > 0, base_profit * ltv_multiplier, base_profit)
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
            'f1, f2, f3, f5, f11, f12 (Logins), f13, f14, f15, f16, f19, f20, f21, f22 (Email Opens).',
            'Profit = BaseProfit * (1.0 + min(f12/50, 0.10) + min(f22/20, 0.05)) IF Base > 0. Base uses 2.5% interchange, 1.5x Risk penalty.',
            'Consolidated LTV strategy: shifts base revenue weights to favor transactors, amplifies risk, and boosts highly engaged users.',
            'Combined macro-financial tuning (interchange vs interest) with digital engagement proxies (logins/emails) for predictive LTV.',
            'Interchange (2.5%), Interest (15%), ECL (1.5x), Primary Fee ($500). LTV capped at +15% boost.',
            'Missing values imputed with 0. Engagement scaled via np.clip to prevent extreme-value rank disruption.',
            'Premium card logic dictates that high-spend/low-risk transactors who engage heavily digitally yield the highest long-term margin.',
            'Assumed digital engagement is highly correlated with retention and lower servicing costs, hence the multiplier for positive accounts.',
            'Comparing against the 0.536 V2 peak. If successful, proves Amex ranks based on predictive LTV, not just historical P&L.',
            'V5 Submission - Comprehensive LTV Engine (Weight Shift + Engagement).'
        ]
    }
    framework_df = pd.DataFrame(framework_data)
  
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        predictions.to_excel(writer, sheet_name='Predictions', index=False)
        framework_df.to_excel(writer, sheet_name='Profitability Framework', index=False)
        
    print(f"Comprehensive V5 Submission successfully generated and saved to: {output_path}")


input_file = r"D:\cv_projects_2\amex_campus_challenge\data\raw\raw_data.csv"
output_file = r"D:\cv_projects_2\amex_campus_challenge\submissions\submission_5.xlsx"
generate_v5_comprehensive(input_file, output_file)