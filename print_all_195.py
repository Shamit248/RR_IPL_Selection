import pandas as pd

df = pd.read_csv('results/temp_uncapped_check.csv')
for idx, r in df.iterrows():
    print(f"{r['player_id']}: {r['player_name']}")

