import pandas as pd
import numpy as np

def generate_v3_submission(input_path, output_path):
    print(f"Loading raw data for V3 from {input_path}...")
    df = pd.read_csv(input_path)
    
    df.fillna(0, inplace=True)
    predictions = pd.DataFrame({'ID': df['id']})
    
    # Rev
    rev_interchange = df['f5'] * 0.02
    rev_interest = df['f1'] * 0.20
    rev_supplementary = df['f19'] * 175
    
    # activating the Base Annual Fee using Active Charge Cards count
    rev_annual_fee = df['f20'] * 625 #mean of 500 and 750 as given in the ref pdf
    
    total_revenue = rev_interchange + rev_interest + rev_supplementary + rev_annual_fee
    
    # cost
    # reconstructing the 5x point generation logic from the PDF to give air and lodging spends extra points 
    # f5 is total spend (1x base). f6 (Air) and f9 (Lodging) get an extra 4x.
    # these are the premium segments where the cc customers get more rewards for spending 
    points_earned = df['f5'] + (df['f6'] * 4) + (df['f9'] * 4)
    
    # Blended Reward Cost (1 percent total =  0.5 percent(redeemed) and 0.5(unredeemed)
    cost_rewards = (points_earned * 0.005) + (df['f21'] * 0.005)
    cost_lounge = df['f13'] * 35      
    cost_cab = df['f15'] * 15         
    cost_air = df['f14']              
    cost_ent = df['f16']              
    
    total_benefits = cost_rewards + cost_lounge + cost_cab + cost_air + cost_ent
    
    # risk 
    expected_loss = df['f1'] * df['f11']
    collection_penalty = df['f3'] * 50000 
    retention_penalty = df['f2'] * 250 
    
    #final Score 
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
            'f1, f2, f3, f5, f6 (Air), f9 (Lodging), f11, f13, f14, f15, f16, f19, f20 (Active Cards), f21.',
            'Profit = BaseRev + (625*f20) - [(f5 + 4*f6 + 4*f9)*0.005 + f21*0.005] - Benefits - RiskPenalty',
            'Incorporates the $625 base annual fee via f20 and calculates the 5x travel reward liabilities.',
            'Activated f6, f9, and f20 to align with the PDF\'s product constraints.',
            'Annual fee set to $625 (mean of $500-$750). Rewards priced at 1c total, split between P&L liability (earned) and cash flow (redeemed).',
            'Missing values (NaNs) imputed with 0.',
            'High travel spenders generate high interchange but incur massive reward liability. Profitability requires offsetting this via fees or low redemption.',
            'f20 maps to the primary annual fee multiplier. Points earned follow the 5x Air/Hotel rule.',
            'Comparing V3 accuracy delta against V2 (0.536) to validate the travel point multiplier hypothesis.',
            'V3 Submission - Activating precision rewards and core card fees.'
        ]
    }
    framework_df = pd.DataFrame(framework_data)
    

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        predictions.to_excel(writer, sheet_name='Predictions', index=False)
        framework_df.to_excel(writer, sheet_name='Profitability Framework', index=False)
        
    print(f"V3 Submission successfully generated and saved to: {output_path}")


input_file = r"D:\cv_projects_2\amex_campus_challenge\data\raw\raw_data.csv"
output_file = r"D:\cv_projects_2\amex_campus_challenge\submissions\submission_3.xlsx"

generate_v3_submission(input_file, output_file)