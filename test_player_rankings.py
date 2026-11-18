import pandas as pd
import numpy as np

# Load bbb
bbb = pd.read_csv('6af3166e7b922_data_pack/ball_by_ball.csv', low_memory=False)
mat = pd.read_csv('6af3166e7b922_data_pack/matches.csv', low_memory=False)
comps = pd.read_csv('6af3166e7b922_data_pack/competitions.csv', low_memory=False)
cmap = pd.read_csv('6af3166e7b922_data_pack/competition_team_player_mapping.csv', low_memory=False)

# Load temp_bbb_pi
pi_df = pd.read_feather('temp_bbb_pi.feather')
bbb['PI'] = pi_df['PI']
bbb['xRuns_bat'] = pi_df['xRuns_bat']
bbb['xRuns_bowl'] = pi_df['xRuns_bowl']
bbb['xWkt_bat'] = pi_df['xWkt_bat']
bbb['xWkt_bowl'] = pi_df['xWkt_bowl']

# Legal flags
bbb['is_batter_legal'] = (bbb['extras_type'] != 'wide').astype(int)
bbb['is_bowler_legal'] = (~bbb['extras_type'].isin(['wide', 'Overstep'])).astype(int)

# Bowler runs conceded = bat runs + wide + noball
wide_noball = bbb['extras_type'].isin(['wide', 'Overstep']).astype(int)
bbb['bowler_runs_conceded'] = bbb['runs'].fillna(0) + wide_noball + bbb['extras_2_runs'].fillna(0)

bowler_wkt_kinds = ['Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket']
bbb['is_bowler_wkt'] = (bbb['is_wicket'] == True) & (bbb['dismissal_type'].isin(bowler_wkt_kinds))
bbb['is_bowler_wkt'] = bbb['is_bowler_wkt'].astype(int)

striker_out = (bbb['is_wicket'] == True) & (
    (bbb['dismissal_type'] != 'RunOut') | (bbb['dismissed_player_id'] == bbb['striker_id'])
)
bbb['is_striker_out'] = striker_out.astype(int)

# Player name map from cmap
player_name_map = cmap.drop_duplicates('player_id').set_index('player_id')['player_name'].to_dict()

# Add names to bbb
bbb['striker_name'] = bbb['striker_id'].map(player_name_map).fillna(bbb['striker_name'])
bbb['bowler_name'] = bbb['bowler_id'].map(player_name_map).fillna(bbb['bowler_name'])

# Pressure split
hp_mask = bbb['PI'] >= 0.65

# ---------------- BATTING EVALUATION ----------------
print("Evaluating batters...")
bat_legal = bbb[bbb['is_batter_legal'] == 1].copy()

# High pressure stats
hp_bat = bat_legal[hp_mask].groupby('striker_id').agg(
    player_name=('striker_name', 'first'),
    hp_matches=('match_id', 'nunique'),
    hp_balls=('is_batter_legal', 'sum'),
    hp_runs=('runs', 'sum'),
    hp_xruns=('xRuns_bat', 'sum'),
    hp_outs=('is_striker_out', 'sum'),
    hp_xwkt=('xWkt_bat', 'sum'),
    hp_fours=('is_four', 'sum'),
    hp_sixes=('is_six', 'sum'),
    hp_dots=('runs', lambda s: (s == 0).sum())
).reset_index()

# Usual (normal) stats (PI < 0.65)
us_bat = bat_legal[~hp_mask].groupby('striker_id').agg(
    us_matches=('match_id', 'nunique'),
    us_balls=('is_batter_legal', 'sum'),
    us_runs=('runs', 'sum'),
    us_xruns=('xRuns_bat', 'sum'),
    us_outs=('is_striker_out', 'sum')
).reset_index()

bat_df = hp_bat.merge(us_bat, on='striker_id', how='left')

# Overall matches
tot_matches = bat_legal.groupby('striker_id')['match_id'].nunique().rename('total_matches')
bat_df = bat_df.merge(tot_matches, on='striker_id', how='left')

# Calculate rates
bat_df['Pressure_SR'] = (bat_df['hp_runs'] / bat_df['hp_balls']) * 100.0
bat_df['Usual_SR'] = np.where(bat_df['us_balls'] >= 20, (bat_df['us_runs'] / bat_df['us_balls']) * 100.0, np.nan)
bat_df['Delta_SR'] = bat_df['Pressure_SR'] - bat_df['Usual_SR']

bat_df['Raw_RAA_100'] = ((bat_df['hp_runs'] - bat_df['hp_xruns']) / bat_df['hp_balls']) * 100.0
bat_df['Pressure_Boundary_Pct'] = ((bat_df['hp_fours'] + bat_df['hp_sixes']) / bat_df['hp_balls']) * 100.0
bat_df['Pressure_Dot_Pct'] = (bat_df['hp_dots'] / bat_df['hp_balls']) * 100.0

# Wicket Preservation: actual outs vs expected outs under pressure
# Ratio: expected outs / max(1, actual outs)
bat_df['Wicket_Preservation'] = bat_df['hp_xwkt'] / bat_df['hp_outs'].clip(lower=1)

# Consistency Score: % of high pressure matches with RAA > 0 (min 5 balls in match)
hp_match_bat = bat_legal[hp_mask].groupby(['striker_id', 'match_id']).agg(
    m_balls=('is_batter_legal', 'sum'),
    m_runs=('runs', 'sum'),
    m_xruns=('xRuns_bat', 'sum')
).reset_index()
hp_match_bat = hp_match_bat[hp_match_bat['m_balls'] >= 5]
hp_match_bat['pos_impact'] = hp_match_bat['m_runs'] > hp_match_bat['m_xruns']

bat_cons = hp_match_bat.groupby('striker_id').agg(
    eval_matches=('pos_impact', 'count'),
    pos_matches=('pos_impact', 'sum')
).reset_index()
bat_cons['Consistency_Pct'] = (bat_cons['pos_matches'] / bat_cons['eval_matches'].clip(lower=1)) * 100.0

bat_df = bat_df.merge(bat_cons[['striker_id', 'Consistency_Pct']], on='striker_id', how='left')
bat_df['Consistency_Pct'] = bat_df['Consistency_Pct'].fillna(40.0)

# Filter for min 120 legal HP balls
bat_120 = bat_df[bat_df['hp_balls'] >= 120].copy()
print(f"Qualified batters (>=120 balls): {len(bat_120)}")

# Empirical Bayes Shrinkage for Batting RAA_100
# Prior mean of qualified peer group
mu_bat_raa = bat_120['Raw_RAA_100'].mean()
K_bat = 40.0
bat_120['shrink_w'] = bat_120['hp_balls'] / (bat_120['hp_balls'] + K_bat)
bat_120['Pressure_RAA_100'] = bat_120['shrink_w'] * bat_120['Raw_RAA_100'] + (1 - bat_120['shrink_w']) * mu_bat_raa

# Composite Clutch Index (Batting):
# Normalize features to 0-100 scale:
# 1. Shrunk RAA_100 (weight 0.40)
# 2. Delta SR (weight 0.25)
# 3. Consistency Pct (weight 0.20)
# 4. Wicket Preservation (weight 0.15)
def min_max_norm(s, clip_q=(0.02, 0.98)):
    lo, hi = s.quantile(clip_q[0]), s.quantile(clip_q[1])
    if hi == lo: return pd.Series(50.0, index=s.index)
    return ((s.clip(lo, hi) - lo) / (hi - lo) * 100.0).clip(0, 100)

s_raa = min_max_norm(bat_120['Pressure_RAA_100'])
s_dsr = min_max_norm(bat_120['Delta_SR'].fillna(0))
s_cons = min_max_norm(bat_120['Consistency_Pct'])
s_wp = min_max_norm(bat_120['Wicket_Preservation'].clip(upper=3.0))

bat_120['Clutch_Index'] = (0.40 * s_raa + 0.25 * s_dsr + 0.20 * s_cons + 0.15 * s_wp).round(2)

print("\nTOP 15 BATTERS (>= 120 HP Balls):")
cols_show = ['striker_id', 'player_name', 'total_matches', 'hp_balls', 'Usual_SR', 'Pressure_SR', 'Delta_SR', 'Pressure_RAA_100', 'Consistency_Pct', 'Clutch_Index']
top_bat = bat_120.sort_values('Clutch_Index', ascending=False).head(15)
print(top_bat[cols_show].to_string(index=False))

