import pandas as pd

files = [
    'top_death_bowlers.csv', 'top_spinners.csv', 'top_allrounders_ranking.csv',
    'top_finishers.csv', 'top_batters_ranking.csv', 'top_bowlers_ranking.csv',
    'young_uncapped_targets.csv'
]

for fname in files:
    df = pd.read_csv(f'results/{fname}')
    print(f"\n--- {fname} (rows: {len(df)}) ---")
    if 'current_active_status' in df.columns:
        print("Statuses:", df['current_active_status'].value_counts().to_dict())
    print(df[['rank', 'player_name', 'determined_role', 'RR_FIT_SCORE', 'pressure_score']].head(5).to_string())
