import pandas as pd
pool = pd.read_csv('results/uncapped_ipl2027_candidate_pool.csv')
pids = [23467, 36982]
sub = pool[pool['player_id'].isin(pids)]
for idx, r in sub.iterrows():
    print(r['player_name'])
    for col in pool.columns:
        if pd.isna(r[col]):
            print(f"  NaN in column: {col}")

