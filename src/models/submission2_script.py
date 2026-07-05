import pandas as pd
import numpy as np

def generate_v2_submission(input_path, output_path):
    print(f"Loading raw data from {input_path}...")
    df = pd.read_csv(input_path)
    
  
    df.fillna(0, inplace=True)
    predictions = pd.DataFrame({'ID': df['id']})
    
    # rev
    rev_interchange = df['f5'] * 0.02
    rev_interest = df['f1'] * 0.20
    # NEW: Supplementary card fee assumption ($175 per extra active card)
    rev_supplementary = df['f19'] * 175
    
    total_revenue = rev_interchange + rev_interest + rev_supplementary
    
    # Cost
    # dropping point cost from 1.5c to 1c to favor high spenders
    cost_rewards = df['f21'] * 0.010 
    
    cost_lounge = df['f13'] * 35      
    cost_cab = df['f15'] * 15         
    cost_air = df['f14']              
    cost_ent = df['f16']              
    
    total_benefits = cost_rewards + cost_lounge + cost_cab + cost_air + cost_ent
    
    # risk
    expected_loss = df['f1'] * df['f11']
    collection_penalty = df['f3'] * 50000 
    
    # cancellation call penalty - it adds up to the cost of a retention offer or lost LTV 
    retention_penalty = df['f2'] * 250 
    
    # Final Score 
    df['Profitability_Score'] = total_revenue - total_benefits - expected_loss - collection_penalty - retention_penalty
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
            'f1, f2 (Cancel Calls), f3, f5, f11, f13, f14, f15, f16, f19 (Supplementary Cards), f21.',
            'Profit = (0.02*f5) + (0.20*f1) + (175*f19) - (0.01*f21) - (35*f13) - (15*f15) - f14 - f16 - (f1*f11) - (50k*f3) - (250*f2)',
            'Base revenue from interchange/interest/supplementary fees, minus benefits/redemptions, minus ECL and retention risks.',
            'Introduced f19 to capture variance in fee revenue, and f2 to capture retention costs/flight risk.',
            'Reduced point liability to 1.0c based on PDF minimum to optimize high-spender rank. Added $175 per f19 based on premium card industry standards.',
            'Missing values (NaNs) imputed with 0 (Structural zeros).',
            'High spenders with supplementary cards drive profit. Heavy redeemers are penalized less in V2. Attrition risk (f2) introduces a new cost vector.',
            'Assumed $175 fee per supplementary card. Assumed a $250 cost associated with general cancellation calls (retention offers).',
            'Public Leaderboard feedback loop. Comparing V2 delta against V1 baseline (0.524).',
            'V2 Submission - Optimizing reward cost weights and supplementary revenue.'
        ]
    }
    framework_df = pd.DataFrame(framework_data)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        predictions.to_excel(writer, sheet_name='Predictions', index=False)
        framework_df.to_excel(writer, sheet_name='Profitability Framework', index=False)
        
    print(f"V2 Submission successfully generated and saved to: {output_path}")

input_file = r"D:\cv_projects_2\amex_campus_challenge\data\raw\raw_data.csv"
output_file = r"D:\cv_projects_2\amex_campus_challenge\submissions\submission_2.xlsx"

generate_v2_submission(input_file, output_file)