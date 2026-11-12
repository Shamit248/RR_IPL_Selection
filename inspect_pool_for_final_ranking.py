"""
inspect_pool_for_final_ranking.py
=================================
Inspect all 477 players, verify player categories, active status,
and test the weight formulation for FINAL_RR_2027_FIT_SCORE.
"""

import pandas as pd
import numpy as np

DATA_DIR = '6af3166e7b922_data_pack'
OUT_DIR  = 'results'

fit = pd.read_csv(f'{OUT_DIR}/player_fit_scores.csv')
status = pd.read_csv(f'{OUT_DIR}/player_status.csv')
uncapped_pool = pd.read_csv(f'{OUT_DIR}/uncapped_ipl2027_candidate_pool.csv')

print(f"Total rows in fit: {len(fit)}")
print(f"Active in status: {len(status[status['current_active_status'] == 'ACTIVE'])}")
print(f"Retired in status: {len(status[status['retirement_status'] == 'RETIRED'])}")
print(f"Uncapped pool rows: {len(uncapped_pool)}")

# Check top performers in fit by existing RR_FIT_SCORE
print("\nTop 20 existing in player_fit_scores:")
print(fit[['player_id', 'player_name', 'determined_role', 'current_active_status', 'RR_FIT_SCORE', 'pressure_score', 'weakness_fit_score']].head(20).to_string())

