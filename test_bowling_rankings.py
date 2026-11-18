import pandas as pd
import numpy as np

# Load bbb
bbb = pd.read_csv('6af3166e7b922_data_pack/ball_by_ball.csv', low_memory=False)
mat = pd.read_csv('6af3166e7b922_data_pack/matches.csv', low_memory=False)
comps = pd.read_csv('6af3166e7b922_data_pack/competitions.csv', low_memory=False)
cmap = pd.read_csv('6af3166e7b922_data_pack/competition_team_player_mapping.csv', low_memory=False)

pi_df = pd.read_feather('temp_bbb_pi.feather')
bbb['PI'] = pi_df['PI']
bbb['xRuns_bowl'] = pi_df['xRuns_bowl']
bbb['xWkt_bowl'] = pi_df['xWkt_bowl']

bbb['is_bowler_legal'] = (~bbb['extras_type'].isin(['wide', 'Overstep'])).astype(int)
wide_noball = bbb['extras_type'].isin(['wide', 'Overstep']).astype(int)
bbb['bowler_runs_conceded'] = bbb['runs'].fillna(0) + wide_noball + bbb['extras_2_runs'].fillna(0)

bowler_wkt_kinds = ['Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket']
bbb['is_bowler_wkt'] = (bbb['is_wicket'] == True) & (bbb['dismissal_type'].isin(bowler_wkt_kinds))
bbb['is_bowler_wkt'] = bbb['is_bowler_wkt'].astype(int)

player_name_map = cmap.drop_duplicates('player_id').set_index('player_id')['player_name'].to_dict()
bbb['bowler_name'] = bbb['bowler_id'].map(player_name_map).fillna(bbb['bowler_name'])

hp_mask = bbb['PI'] >= 0.65
bowl_legal = bbb[bbb['is_bowler_legal'] == 1].copy()
hp_mask_sub = hp_mask.loc[bowl_legal.index]

# High pressure stats
hp_bowl = bowl_legal[hp_mask_sub].groupby('bowler_id').agg(
    player_name=('bowler_name', 'first'),
    hp_matches=('match_id', 'nunique'),
    hp_balls=('is_bowler_legal', 'sum'),
    hp_runs_conceded=('bowler_runs_conceded', 'sum'),
    hp_xruns=('xRuns_bowl', 'sum'),
    hp_wkts=('is_bowler_wkt', 'sum'),
    hp_xwkt=('xWkt_bowl', 'sum'),
    hp_dots=('bowler_runs_conceded', lambda s: (s == 0).sum()),
    hp_boundaries=('is_four', lambda s: (s == 1).sum()) # we'll add sixes too
).reset_index()

# Add sixes
sixes_hp = bowl_legal[hp_mask_sub].groupby('bowler_id')['is_six'].apply(lambda s: (s == 1).sum()).reset_index()
hp_bowl['hp_boundaries'] += sixes_hp['is_six']

# Usual (normal) stats
us_bowl = bowl_legal[~hp_mask_sub].groupby('bowler_id').agg(
    us_matches=('match_id', 'nunique'),
    us_balls=('is_bowler_legal', 'sum'),
    us_runs_conceded=('bowler_runs_conceded', 'sum'),
    us_wkts=('is_bowler_wkt', 'sum')
).reset_index()

bowl_df = hp_bowl.merge(us_bowl, on='bowler_id', how='left')
tot_matches = bowl_legal.groupby('bowler_id')['match_id'].nunique().rename('total_matches')
bowl_df = bowl_df.merge(tot_matches, on='bowler_id', how='left')

# Rates
bowl_df['Pressure_Econ'] = (bowl_df['hp_runs_conceded'] / (bowl_df['hp_balls'] / 6.0))
bowl_df['Usual_Econ'] = np.where(bowl_df['us_balls'] >= 24, (bowl_df['us_runs_conceded'] / (bowl_df['us_balls'] / 6.0)), np.nan)
bowl_df['Delta_Econ'] = bowl_df['Usual_Econ'] - bowl_df['Pressure_Econ']

bowl_df['Raw_RSAE_24'] = ((bowl_df['hp_xruns'] - bowl_df['hp_runs_conceded']) / bowl_df['hp_balls']) * 24.0
bowl_df['Wickets_Above_Exp'] = bowl_df['hp_wkts'] - bowl_df['hp_xwkt']
bowl_df['Pressure_Dot_Pct'] = (bowl_df['hp_dots'] / bowl_df['hp_balls']) * 100.0
bowl_df['Pressure_Bnd_Conceded_Pct'] = (bowl_df['hp_boundaries'] / bowl_df['hp_balls']) * 100.0

# Consistency Score: % of matches with >= 6 balls where RSAE > 0
hp_match_bowl = bowl_legal[hp_mask_sub].groupby(['bowler_id', 'match_id']).agg(
    m_balls=('is_bowler_legal', 'sum'),
    m_runs=('bowler_runs_conceded', 'sum'),
    m_xruns=('xRuns_bowl', 'sum')
).reset_index()
hp_match_bowl = hp_match_bowl[hp_match_bowl['m_balls'] >= 6]
hp_match_bowl['pos_impact'] = hp_match_bowl['m_xruns'] > hp_match_bowl['m_runs']

bowl_cons = hp_match_bowl.groupby('bowler_id').agg(
    eval_matches=('pos_impact', 'count'),
    pos_matches=('pos_impact', 'sum')
).reset_index()
bowl_cons['Consistency_Pct'] = (bowl_cons['pos_matches'] / bowl_cons['eval_matches'].clip(lower=1)) * 100.0
bowl_df = bowl_df.merge(bowl_cons[['bowler_id', 'Consistency_Pct']], on='bowler_id', how='left')
bowl_df['Consistency_Pct'] = bowl_df['Consistency_Pct'].fillna(40.0)

# Filter for min 120 legal HP balls
bowl_120 = bowl_df[bowl_df['hp_balls'] >= 120].copy()
print(f"Qualified bowlers (>=120 balls): {len(bowl_120)}")

# Empirical Bayes Shrinkage for Bowling RSAE_24
mu_bowl_rsae = bowl_120['Raw_RSAE_24'].mean()
K_bowl = 40.0
bowl_120['shrink_w'] = bowl_120['hp_balls'] / (bowl_120['hp_balls'] + K_bowl)
bowl_120['Pressure_RSAE_24'] = bowl_120['shrink_w'] * bowl_120['Raw_RSAE_24'] + (1 - bowl_120['shrink_w']) * mu_bowl_rsae

def min_max_norm(s, clip_q=(0.02, 0.98)):
    lo, hi = s.quantile(clip_q[0]), s.quantile(clip_q[1])
    if hi == lo: return pd.Series(50.0, index=s.index)
    return ((s.clip(lo, hi) - lo) / (hi - lo) * 100.0).clip(0, 100)

s_rsae = min_max_norm(bowl_120['Pressure_RSAE_24'])
s_decon = min_max_norm(bowl_120['Delta_Econ'].fillna(0))
s_bcons = min_max_norm(bowl_120['Consistency_Pct'])
s_wae = min_max_norm(bowl_120['Wickets_Above_Exp'].clip(lower=-5, upper=15))

bowl_120['Clutch_Index'] = (0.40 * s_rsae + 0.25 * s_decon + 0.20 * s_bcons + 0.15 * s_wae).round(2)

print("\nTOP 15 BOWLERS (>= 120 HP Balls):")
cols_show = ['bowler_id', 'player_name', 'total_matches', 'hp_balls', 'Usual_Econ', 'Pressure_Econ', 'Delta_Econ', 'Pressure_RSAE_24', 'Wickets_Above_Exp', 'Consistency_Pct', 'Clutch_Index']
top_bowl = bowl_120.sort_values('Clutch_Index', ascending=False).head(15)
print(top_bowl[cols_show].to_string(index=False))

