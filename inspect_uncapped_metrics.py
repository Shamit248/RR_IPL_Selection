"""
inspect_uncapped_metrics.py
===========================
Check available metrics in results CSVs for our uncapped candidate pool.
"""

import pandas as pd

DATA_DIR = '6af3166e7b922_data_pack'
OUT_DIR  = 'results'

bat = pd.read_csv(f'{OUT_DIR}/player_batting_metrics.csv')
bowl = pd.read_csv(f'{OUT_DIR}/player_bowling_metrics.csv')
press = pd.read_csv(f'{OUT_DIR}/pressure_player_metrics.csv')
rel = pd.read_csv(f'{OUT_DIR}/player_reliability.csv')
roles = pd.read_csv(f'{OUT_DIR}/player_role_analysis.csv')
fit = pd.read_csv(f'{OUT_DIR}/player_fit_scores.csv')

print("Batting cols:", [c for c in bat.columns if 'pressure' in c or 'death' in c or 'sr' in c or 'run' in c][:10])
print("Bowling cols:", [c for c in bowl.columns if 'pressure' in c or 'death' in c or 'econ' in c or 'wkt' in c][:10])
print("Pressure cols:", list(press.columns))
print("Reliability cols:", list(rel.columns))
print("Roles cols:", list(roles.columns))

