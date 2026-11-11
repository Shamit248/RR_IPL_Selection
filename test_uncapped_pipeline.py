"""
test_uncapped_pipeline.py
=========================
Prototype for building the uncapped candidate pool and fit scores.
"""

import os
import pandas as pd
import numpy as np

DATA_DIR = '6af3166e7b922_data_pack'
OUT_DIR  = 'results'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
teams    = pd.read_csv(f'{DATA_DIR}/teams.csv')
comps    = pd.read_csv(f'{DATA_DIR}/competitions.csv')
pe       = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')
bbb      = pd.read_csv(f'{DATA_DIR}/ball_by_ball.csv', usecols=['match_id', 'striker_id', 'bowler_id', 'runs_off_bat', 'extras_2_runs', 'is_wicket', 'over_num'])

fit      = pd.read_csv(f'{OUT_DIR}/player_fit_scores.csv')
status   = pd.read_csv(f'{OUT_DIR}/player_status.csv')
press    = pd.read_csv(f'{OUT_DIR}/pressure_player_metrics.csv')
rel      = pd.read_csv(f'{OUT_DIR}/player_reliability.csv')
roles    = pd.read_csv(f'{OUT_DIR}/player_role_analysis.csv')
weak     = pd.read_csv(f'{OUT_DIR}/rr_weaknesses.csv')

print("Loaded all base data. Constructing nationality & cap mappings...")
