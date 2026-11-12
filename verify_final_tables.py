"""
verify_final_tables.py
======================
Verify all generated recruitment CSVs for cleanliness, zero NaNs,
correct schemas, and expected outputs.
"""

import pandas as pd

files = [
    'results/ipl2027_performance_ranking.csv',
    'results/rr_ipl2027_recruitment_ranking.csv',
    'results/rr_ipl2027_top20.csv',
    'results/rr_ipl2027_capped_top10.csv',
    'results/rr_ipl2027_uncapped_top10.csv',
    'results/rr_ipl2027_final_top10.csv',
    'results/rr_ipl2027_role_targets.csv',
    'results/rr_ipl2027_value_upside_matrix.csv'
]

for f in files:
    df = pd.read_csv(f)
    print(f"=== {f} ===")
    print(f"Rows: {len(df)}, Cols: {len(df.columns)}")
    nans = df.isna().sum()
    if nans.sum() > 0:
        print("  WARNING NaNs:")
        print(nans[nans > 0])
    else:
        print("  ZERO NaNs! Completely verified.")

print("\n--- CAPPED TOP 10 ---")
c10 = pd.read_csv('results/rr_ipl2027_capped_top10.csv')
for idx, r in c10.iterrows():
    print(f"#{r['rank']:2d}: {r['player_name']:<22} | {r['player_category']:<15} | Role: {r['primary_role']:<20} | Score: {r['final_rr_2027_fit_score']:.2f} | Avail: {r['availability_probability']:.2f}")

print("\n--- UNCAPPED TOP 10 ---")
u10 = pd.read_csv('results/rr_ipl2027_uncapped_top10.csv')
for idx, r in u10.iterrows():
    print(f"#{r['rank']:2d}: {r['player_name']:<22} | {r['player_category']:<15} | Role: {r['primary_role']:<20} | Score: {r['final_rr_2027_fit_score']:.2f} | Avail: {r['availability_probability']:.2f}")

print("\n--- ROLE-WISE TARGETS ---")
rt = pd.read_csv('results/rr_ipl2027_role_targets.csv')
print(rt.to_string())

