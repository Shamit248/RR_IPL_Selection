import pandas as pd
import numpy as np
from scipy.stats import spearmanr

# Load bbb with PI and models
bbb = pd.read_csv('6af3166e7b922_data_pack/ball_by_ball.csv', low_memory=False)
pi_df = pd.read_feather('temp_bbb_pi.feather')
bbb['PI'] = pi_df['PI']
bbb['xRuns_bat'] = pi_df['xRuns_bat']
bbb['xRuns_bowl'] = pi_df['xRuns_bowl']
bbb['xWkt_bat'] = pi_df['xWkt_bat']
bbb['xWkt_bowl'] = pi_df['xWkt_bowl']

bbb['is_batter_legal'] = (bbb['extras_type'] != 'wide').astype(int)
bbb['is_bowler_legal'] = (~bbb['extras_type'].isin(['wide', 'Overstep'])).astype(int)
wide_noball = bbb['extras_type'].isin(['wide', 'Overstep']).astype(int)
bbb['bowler_runs_conceded'] = bbb['runs'].fillna(0) + wide_noball + bbb['extras_2_runs'].fillna(0)
bowler_wkt_kinds = ['Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket']
bbb['is_bowler_wkt'] = (bbb['is_wicket'] == True) & (bbb['dismissal_type'].isin(bowler_wkt_kinds))
bbb['is_bowler_wkt'] = bbb['is_bowler_wkt'].astype(int)

striker_out = (bbb['is_wicket'] == True) & (
    (bbb['dismissal_type'] != 'RunOut') | (bbb['dismissed_player_id'] == bbb['striker_id'])
)
bbb['is_striker_out'] = striker_out.astype(int)

def rank_batters(pi_thresh=0.65, min_balls=120):
    hp_mask = bbb['PI'] >= pi_thresh
    bat_legal = bbb[bbb['is_batter_legal'] == 1]
    
    hp = bat_legal[hp_mask].groupby('striker_id').agg(
        hp_balls=('is_batter_legal', 'sum'),
        hp_runs=('runs', 'sum'),
        hp_xruns=('xRuns_bat', 'sum'),
        hp_outs=('is_striker_out', 'sum'),
        hp_xwkt=('xWkt_bat', 'sum')
    ).reset_index()
    
    us = bat_legal[~hp_mask].groupby('striker_id').agg(
        us_balls=('is_batter_legal', 'sum'),
        us_runs=('runs', 'sum')
    ).reset_index()
    
    m = hp.merge(us, on='striker_id', how='left')
    m = m[m['hp_balls'] >= min_balls].copy()
    
    m['Pressure_SR'] = (m['hp_runs'] / m['hp_balls']) * 100.0
    m['Usual_SR'] = (m['us_runs'] / m['us_balls'].clip(lower=1)) * 100.0
    m['Delta_SR'] = m['Pressure_SR'] - m['Usual_SR']
    m['Raw_RAA_100'] = ((m['hp_runs'] - m['hp_xruns']) / m['hp_balls']) * 100.0
    
    mu = m['Raw_RAA_100'].mean()
    w = m['hp_balls'] / (m['hp_balls'] + 40.0)
    m['Pressure_RAA_100'] = w * m['Raw_RAA_100'] + (1 - w) * mu
    
    # rank score
    s_r = (m['Pressure_RAA_100'] - m['Pressure_RAA_100'].mean()) / m['Pressure_RAA_100'].std()
    s_d = (m['Delta_SR'] - m['Delta_SR'].mean()) / m['Delta_SR'].std()
    m['score'] = 0.6 * s_r + 0.4 * s_d
    return m.sort_values('score', ascending=False).set_index('striker_id')['score']

# Baseline
base_bat = rank_batters(0.65, 120)

results = []
for p in [0.60, 0.65, 0.70]:
    for b in [100, 120, 150]:
        alt = rank_batters(p, b)
        common = base_bat.index.intersection(alt.index)
        rho, _ = spearmanr(base_bat.loc[common], alt.loc[common])
        results.append({'PI_Cutoff': p, 'Min_Balls': b, 'Common_Players': len(common), 'Spearman_Rho': round(rho, 3)})

print("Sensitivity Analysis for Batting:")
print(pd.DataFrame(results))

