"""
generate_dual_rankings.py
=========================
Generates:
  1. results/historical_top10_batters.csv
  2. results/historical_top10_bowlers.csv
  3. results/ipl2027_eligible_top10_batters.csv
  4. results/ipl2027_eligible_top10_bowlers.csv
  5. results/ipl2027_status_unknown_watchlist.csv
"""

import os
import numpy as np
import pandas as pd

OUT_DIR = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\results'

press = pd.read_csv(os.path.join(OUT_DIR, 'pressure_player_metrics.csv'))
rel   = pd.read_csv(os.path.join(OUT_DIR, 'player_reliability.csv'))
roles = pd.read_csv(os.path.join(OUT_DIR, 'player_role_analysis.csv'))
status= pd.read_csv(os.path.join(OUT_DIR, 'player_status.csv'))

# 1. PREPARE BATTERS
# Filter press for player_type == 'batter'
press_bat = press[press['player_type'] == 'batter'].copy()
press_bat = press_bat.merge(rel[['player_id', 'reliability_score_bat']], on='player_id', how='left')
press_bat = press_bat.merge(roles[['player_id', 'primary_role']].rename(columns={'primary_role': 'determined_role'}), on='player_id', how='left')
press_bat = press_bat.merge(status[['player_id', 'current_active_status', 'retirement_status', 'ipl_2027_status', 'eligibility_reason', 'final_eligible']], on='player_id', how='left')

# Deduplicate by player_id
press_bat = press_bat.drop_duplicates(subset=['player_id']).copy()

# Sample filter: min 30 pressure balls
press_bat = press_bat[press_bat['pressure_balls'] >= 30].copy()

def norm_series(s):
    mi, ma = s.quantile(0.05), s.quantile(0.95)
    if ma == mi:
        return pd.Series(50.0, index=s.index)
    return ((s.clip(mi, ma) - mi) / (ma - mi) * 100).clip(0, 100)

def inv_norm_series(s):
    return 100 - norm_series(s)

# Composite Batting Pressure Score
s_sr = norm_series(press_bat['pressure_SR'].fillna(120))
s_dsr= norm_series(press_bat['pressure_delta_SR'].fillna(0))
s_avg= norm_series(press_bat['pressure_avg'].clip(upper=60).fillna(20))
s_rel= norm_series(press_bat['reliability_score_bat'].fillna(50))

press_bat['bat_pressure_score'] = (
    0.40 * s_sr +
    0.20 * s_dsr +
    0.20 * s_avg +
    0.20 * s_rel
).round(2)

# Population A: Historical Top 10 Batters (All players)
hist_bat_10 = press_bat.sort_values('bat_pressure_score', ascending=False).head(10).copy()
hist_bat_10['rank'] = range(1, len(hist_bat_10) + 1)
hist_bat_cols = [
    'rank', 'player_id', 'player_name', 'determined_role', 
    'pressure_balls', 'pressure_SR', 'pressure_delta_SR', 'pressure_avg', 
    'pressure_boundary_rate', 'reliability_score_bat', 'bat_pressure_score', 
    'current_active_status', 'final_eligible'
]
hist_bat_10[hist_bat_cols].to_csv(os.path.join(OUT_DIR, 'historical_top10_batters.csv'), index=False)
print("Saved historical_top10_batters.csv")
print(hist_bat_10[hist_bat_cols].to_string())

# Population B: Eligible Top 10 Batters (final_eligible == TRUE)
elig_bat = press_bat[press_bat['final_eligible'] == 'TRUE'].copy()
elig_bat_10 = elig_bat.sort_values('bat_pressure_score', ascending=False).head(10).copy()
elig_bat_10['rank'] = range(1, len(elig_bat_10) + 1)
elig_bat_cols = [
    'rank', 'player_id', 'player_name', 'determined_role', 
    'pressure_balls', 'pressure_SR', 'pressure_delta_SR', 'pressure_avg', 
    'pressure_boundary_rate', 'reliability_score_bat', 'bat_pressure_score', 
    'ipl_2027_status', 'eligibility_reason'
]
elig_bat_10[elig_bat_cols].to_csv(os.path.join(OUT_DIR, 'ipl2027_eligible_top10_batters.csv'), index=False)
print("\nSaved ipl2027_eligible_top10_batters.csv")
print(elig_bat_10[elig_bat_cols].to_string())

# 2. PREPARE BOWLERS
press_bowl = press[press['player_type'] == 'bowler'].copy()
press_bowl = press_bowl.merge(rel[['player_id', 'reliability_score_bowl']], on='player_id', how='left')
press_bowl = press_bowl.merge(roles[['player_id', 'primary_role']].rename(columns={'primary_role': 'determined_role'}), on='player_id', how='left')
press_bowl = press_bowl.merge(status[['player_id', 'current_active_status', 'retirement_status', 'ipl_2027_status', 'eligibility_reason', 'final_eligible']], on='player_id', how='left')

# Deduplicate
press_bowl = press_bowl.drop_duplicates(subset=['player_id']).copy()

# Sample filter: min 30 deliveries bowled
bowl_metrics = pd.read_csv(os.path.join(OUT_DIR, 'player_bowling_metrics.csv'))
if 'balls_bowled' in bowl_metrics.columns:
    press_bowl = press_bowl.merge(bowl_metrics[['bowler_id', 'balls_bowled']].rename(columns={'bowler_id': 'player_id'}), on='player_id', how='left')
else:
    press_bowl['balls_bowled'] = 100

press_bowl = press_bowl[press_bowl['balls_bowled'] >= 30].copy()
press_bowl = press_bowl[press_bowl['pressure_economy'].notna()].copy()

# Composite Bowling Pressure Score
b_eco  = inv_norm_series(press_bowl['pressure_economy'].fillna(9.5))
b_wkt  = norm_series(press_bowl['pressure_wicket_rate'].fillna(0.04))
b_deco = inv_norm_series(press_bowl['pressure_delta_economy'].fillna(0))
b_rel  = norm_series(press_bowl['reliability_score_bowl'].fillna(50))

press_bowl['bowl_pressure_score'] = (
    0.35 * b_eco +
    0.25 * b_wkt +
    0.20 * b_deco +
    0.20 * b_rel
).round(2)

# Population A: Historical Top 10 Bowlers
hist_bowl_10 = press_bowl.sort_values('bowl_pressure_score', ascending=False).head(10).copy()
hist_bowl_10['rank'] = range(1, len(hist_bowl_10) + 1)
hist_bowl_cols = [
    'rank', 'player_id', 'player_name', 'determined_role', 
    'balls_bowled', 'pressure_economy', 'pressure_delta_economy', 
    'pressure_wicket_rate', 'pressure_dot_rate', 'reliability_score_bowl', 
    'bowl_pressure_score', 'current_active_status', 'final_eligible'
]
hist_bowl_10[hist_bowl_cols].to_csv(os.path.join(OUT_DIR, 'historical_top10_bowlers.csv'), index=False)
print("\nSaved historical_top10_bowlers.csv")
print(hist_bowl_10[hist_bowl_cols].to_string())

# Population B: Eligible Top 10 Bowlers
elig_bowl = press_bowl[press_bowl['final_eligible'] == 'TRUE'].copy()
elig_bowl_10 = elig_bowl.sort_values('bowl_pressure_score', ascending=False).head(10).copy()
elig_bowl_10['rank'] = range(1, len(elig_bowl_10) + 1)
elig_bowl_cols = [
    'rank', 'player_id', 'player_name', 'determined_role', 
    'balls_bowled', 'pressure_economy', 'pressure_delta_economy', 
    'pressure_wicket_rate', 'pressure_dot_rate', 'reliability_score_bowl', 
    'bowl_pressure_score', 'ipl_2027_status', 'eligibility_reason'
]
elig_bowl_10[elig_bowl_cols].to_csv(os.path.join(OUT_DIR, 'ipl2027_eligible_top10_bowlers.csv'), index=False)
print("\nSaved ipl2027_eligible_top10_bowlers.csv")
print(elig_bowl_10[elig_bowl_cols].to_string())

# 3. WATCHLIST FOR UNCERTAIN / UNKNOWN PLAYERS
watchlist = status[status['final_eligible'] == 'UNKNOWN'].copy()
watch_cols = [
    'player_id', 'player_name', 'last_ipl_season', 'last_t20i_season',
    'current_active_status', 'retirement_status', 'ipl_2027_status',
    'status_source', 'status_date', 'eligibility_reason', 'final_eligible'
]
watchlist[watch_cols].to_csv(os.path.join(OUT_DIR, 'ipl2027_status_unknown_watchlist.csv'), index=False)
print(f"\nSaved ipl2027_status_unknown_watchlist.csv ({len(watchlist)} players)")
