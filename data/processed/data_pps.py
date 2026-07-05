import pandas as pd
import numpy as np

def generate_data_xray(file_path):
    try:
        df = pd.read_excel(file_path) 
    except Exception as e:
        return f"Error loading file: {e}"

    print("\n--- DATA X-RAY REPORT ---")
    print(f"\n1. Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    missing_data = df.isnull().sum()
    missing_percent = (missing_data / len(df)) * 100
    missing_df = pd.DataFrame({'Missing Count': missing_data, 'Percentage': missing_percent})
    missing_df = missing_df[missing_df['Missing Count'] > 0].sort_values(by='Percentage', ascending=False)
    
    print("\n2. Missing Value Percentages (Top Variables):")
    if missing_df.empty:
        print("No missing values found!")
    else:
        print(missing_df.head(15).round(2).to_string())
    
    features = [col for col in df.columns if col != 'id']
    desc = df[features].describe(percentiles=[.25, .50, .75, .95, .99]).T
    print("\n3. Feature Distributions (Snippets of extremes):")
    # we specifically want to look for heavy skewness (where max is much higher than 99th percentile)
    desc['Skew_Warning'] = np.where(desc['max'] > (desc['99%'] * 5), "High Skew", "Normal")
    print(desc[['mean', '50%', '99%', 'max', 'Skew_Warning']].round(2).to_string())

if __name__ == "__main__":
    file_path = r"D:\cv_projects_2\amex_campus_challenge\data\raw\raw_data.csv"
    generate_data_xray(file_path)