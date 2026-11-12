"""
check_final_pipeline_inputs.py
==============================
Verify all input columns, sample sizes, and candidate data across fit_df,
pressure_metrics, reliability, roles, and status.
"""

import pandas as pd
import numpy as np

fit = pd.read_csv('results/player_fit_scores.csv')
status = pd.read_csv('results/player_status.csv')
roles = pd.read_csv('results/player_role_analysis.csv')
press = pd.read_csv('results/pressure_player_metrics.csv')
rel = pd.read_csv('results/player_reliability.csv')
weak = pd.read_csv('results/rr_weaknesses.csv')

print(f"Fit rows: {len(fit)}")
print(f"Status rows: {len(status)}")
print(f"Roles rows: {len(roles)}")
print(f"Press rows: {len(press)}")
print(f"Rel rows: {len(rel)}")
print(f"Weakness count: {len(weak)}")

# Check key metric distributions in fit
cols_to_check = [
    'pressure_score', 'weakness_fit_score', 'role_fit_score',
    'ipl_performance_score', 'recent_form_score', 'reliability_score_unified',
    'venue_fit_score', 'upside_score', 'balls_faced', 'balls_bowled'
]
for col in cols_to_check:
    if col in fit.columns:
        print(f"{col:28s}: min={fit[col].min():.2f}, max={fit[col].max():.2f}, na={fit[col].isna().sum()}")
    else:
        print(f"{col:28s}: NOT FOUND")

