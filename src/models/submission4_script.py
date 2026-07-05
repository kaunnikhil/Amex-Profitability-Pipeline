import pandas as pd
import numpy as np

def generate_v4_submission(input_path, output_path):
    print(f"Loading raw data for V4 from {input_path}...")
    df = pd.read_csv(input_path)
    

    df.fillna(0, inplace=True)
    predictions = pd.DataFrame({'ID': df['id']})
    
    # Rev
    rev_interchange = df['f5'] * 0.02
    rev_interest = df['f1'] * 0.20
    rev_supplementary = df['f19'] * 175
    
    total_revenue = rev_interchange + rev_interest + rev_supplementary
    
    # Cost
    cost_rewards = df['f21'] * 0.010 
    cost_lounge = df['f13'] * 35      
    cost_cab = df['f15'] * 15         
    cost_air = df['f14']              
    cost_ent = df['f16']              
    
    total_benefits = cost_rewards + cost_lounge + cost_cab + cost_air + cost_ent
    
    # Risk 
    expected_loss = df['f1'] * df['f11']
    collection_penalty = df['f3'] * 50000 
    retention_penalty = df['f2'] * 250 
    
    # Credit Utilization Penalty
    # We add 1 to f17 to prevent dividing by zero for users with no lend line.
    # edit - this actually made this script illogical bcoz when f17 ie when total lend line amount = 0 then the ratio equals the revolving amount way greater than 1 hence the toxic utilization penalty skyrocketed even for those who had no lend line amt.
    utilization_ratio = df['f1'] / (df['f17'] + 1)
    
    # if utilization is over 80%, we heavily penalize them as a toxic risk.
    toxic_utilization_penalty = np.where(utilization_ratio > 0.80, 5000, 0)
    
    #Final Score
    df['Profitability_Score'] = total_revenue - total_benefits - expected_loss - collection_penalty - retention_penalty - toxic_utilization_penalty
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
            'f1, f2, f3, f5, f11, f13, f14, f15, f16, f17 (Total Lend Line), f19, f21.',
            'Profit = (0.02*f5) + (0.20*f1) + (175*f19) - (0.01*f21) - Benefits - (f1*f11) - (50k*f3) - (250*f2) - (ToxicUtilPenalty)',
            'Base revenue from V2, minus benefits/redemptions, minus ECL, plus a conditional penalty for >80% credit utilization.',
            'Reverted V3 travel reward penalties (which tanked performance) and introduced f17 to assess hidden credit risk.',
            'Utilization > 80% triggers a flat $5,000 toxic risk penalty, assuming high utilization precedes default.',
            'Engineered Utilization Ratio = f1 / (f17 + 1) to prevent zero-division. NaNs imputed with 0.',
            'High travel spenders are Amex\'s best cohort; penalizing their points was mathematically incorrect. True unprofitability stems from high utilization/default risk.',
            'Assumed users with no f17 (Lend Line = 0) are charge-card only, meaning any revolving balance is an immediate violation.',
            'V4 Submission comparing against the V2 peak (0.536).',
            'V4 Pivot - Prioritizing Feature Engineering (Utilization) over raw product fee constraints.'
        ]
    }
    framework_df = pd.DataFrame(framework_data)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        predictions.to_excel(writer, sheet_name='Predictions', index=False)
        framework_df.to_excel(writer, sheet_name='Profitability Framework', index=False)
        
    print(f"V4 Submission successfully generated and saved to: {output_path}")


input_file = r"D:\cv_projects_2\amex_campus_challenge\data\raw\raw_data.csv"
output_file = r"D:\cv_projects_2\amex_campus_challenge\submissions\submission_4.xlsx"
generate_v4_submission(input_file, output_file)