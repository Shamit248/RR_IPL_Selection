import pandas as pd
import numpy as np
import lightgbm as lgb
from scipy.stats import spearmanr
import warnings
warnings.filterwarnings('ignore')

print("--- 1. LOADING AND PREPARING DATA ---")
bbb = pd.read_csv('6af3166e7b922_data_pack/ball_by_ball.csv', low_memory=False)
mat = pd.read_csv('6af3166e7b922_data_pack/matches.csv', low_memory=False)
comps = pd.read_csv('6af3166e7b922_data_pack/competitions.csv', low_memory=False)
cmap = pd.read_csv('6af3166e7b922_data_pack/competition_team_player_mapping.csv', low_memory=False)

# Clean super overs
bbb = bbb[bbb['innings'].isin([1, 2])].copy()
bbb = bbb.sort_values(['match_id', 'innings', 'innings_ball_num']).reset_index(drop=True)

# Merge match metadata
mat_cols = ['match_id', 'comp_id', 'match_number', 'match_date', 'stage', 'venue_id', 'venue_country',
            'home_team_id', 'away_team_id', 'knock_out', 'win_team_id', 'result',
            'first_inn_revised_overs', 'second_inn_revised_overs', 'revised_target']
mat_sub = mat[[c for c in mat_cols if c in mat.columns]].drop_duplicates('match_id')
bbb = bbb.merge(mat_sub, on='match_id', how='left')

# Exclude abandoned matches with no result
bbb = bbb[bbb['result'].notna()].copy()

# Legal balls
bbb['is_batter_legal'] = (bbb['extras_type'] != 'wide').astype(int)
bbb['is_bowler_legal'] = (~bbb['extras_type'].isin(['wide', 'Overstep'])).astype(int)

# Runs
extra_run = bbb['extras_type'].isin(['wide', 'Overstep', 'legbyes', 'byes', 'other']).astype(int)
penalty_run = (bbb['extras_type'] == 'Penalty').astype(int) * 5
bbb['team_runs_ball'] = bbb['runs'].fillna(0) + bbb['extras_2_runs'].fillna(0) + extra_run + penalty_run

# Bowler runs conceded = bat runs + wide + noball (legbyes and byes are not charged to bowler)
wide_noball = bbb['extras_type'].isin(['wide', 'Overstep']).astype(int)
bbb['bowler_runs_conceded'] = bbb['runs'].fillna(0) + wide_noball + bbb['extras_2_runs'].fillna(0)

# Bowler wicket (excludes run outs, retire outs, etc.)
bowler_wkt_kinds = ['Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket']
bbb['is_bowler_wkt'] = (bbb['is_wicket'] == True) & (bbb['dismissal_type'].isin(bowler_wkt_kinds))
bbb['is_bowler_wkt'] = bbb['is_bowler_wkt'].astype(int)

# Striker dismissal (exclude non-striker run outs)
striker_out = (bbb['is_wicket'] == True) & (
    (bbb['dismissal_type'] != 'RunOut') | (bbb['dismissed_player_id'] == bbb['striker_id'])
)
bbb['is_striker_out'] = striker_out.astype(int)

# Cumulative match state
grp = bbb.groupby(['match_id', 'innings'], sort=False)
bbb['score_before'] = grp['team_runs_ball'].transform(lambda s: s.cumsum().shift(1).fillna(0))
bbb['wickets_lost_before'] = grp['is_wicket'].transform(lambda s: s.cumsum().shift(1).fillna(0)).astype(int)
bbb['legal_balls_bowled'] = grp['is_bowler_legal'].transform(lambda s: s.cumsum().shift(1).fillna(0)).astype(int)

bbb['max_overs_balls'] = 120
mask_rev_inn1 = (bbb['innings'] == 1) & bbb['first_inn_revised_overs'].notna() & (bbb['first_inn_revised_overs'] > 0)
bbb.loc[mask_rev_inn1, 'max_overs_balls'] = bbb.loc[mask_rev_inn1, 'first_inn_revised_overs']

mask_rev_inn2 = (bbb['innings'] == 2) & bbb['second_inn_revised_overs'].notna() & (bbb['second_inn_revised_overs'] > 0)
bbb.loc[mask_rev_inn2, 'max_overs_balls'] = bbb.loc[mask_rev_inn2, 'second_inn_revised_overs']

bbb['balls_remaining'] = (bbb['max_overs_balls'] - bbb['legal_balls_bowled']).clip(lower=0)

inn1_totals = bbb[bbb['innings'] == 1].groupby('match_id')['team_runs_ball'].sum().rename('inn1_total')
bbb = bbb.merge(inn1_totals, on='match_id', how='left')

bbb['target'] = np.where(bbb['innings'] == 2, bbb['inn1_total'] + 1, np.nan)
mask_rev_target = (bbb['innings'] == 2) & bbb['revised_target'].notna() & (bbb['revised_target'] > 0)
bbb.loc[mask_rev_target, 'target'] = bbb.loc[mask_rev_target, 'revised_target']

bbb['runs_required'] = np.where(bbb['innings'] == 2, (bbb['target'] - bbb['score_before']).clip(lower=0), np.nan)
bbb['rrr'] = np.where(
    (bbb['innings'] == 2) & (bbb['balls_remaining'] > 0),
    (bbb['runs_required'] / bbb['balls_remaining']) * 6.0,
    np.where(bbb['innings'] == 2, 0.0, np.nan)
)

print("--- 2. COMPUTING PRESSURE INDEX ---")
# Innings 2:
p_eq = ((bbb['rrr'] - 6.5) / (16.5 - 6.5)).clip(0, 1)
res_ratio = ((10.0 - bbb['wickets_lost_before']) / 10.0) * (bbb['balls_remaining'] / bbb['max_overs_balls'].replace(0, 120))
p_scarcity = (1.0 - res_ratio).clip(0, 1)
closeness_bell = np.exp(-0.5 * ((bbb['rrr'] - 11.5) / 4.0) ** 2)

dead_win = (bbb['runs_required'] <= 6) & (bbb['balls_remaining'] >= 18) & (bbb['wickets_lost_before'] <= 4)
dead_loss = ((bbb['balls_remaining'] <= 6) & (bbb['runs_required'] >= 36)) | \
            ((bbb['balls_remaining'] <= 12) & (bbb['runs_required'] >= 48)) | \
            ((bbb['wickets_lost_before'] >= 9) & (bbb['runs_required'] >= 24) & (bbb['balls_remaining'] <= 12))

closeness_weight = closeness_bell.copy()
closeness_weight = np.where(dead_win | dead_loss, 0.10, closeness_weight)

pi_inn2 = 0.45 * p_eq + 0.35 * p_scarcity + 0.20 * closeness_weight
pi_inn2 = np.where(dead_win | dead_loss, np.minimum(pi_inn2, 0.30), pi_inn2)

# Innings 1:
c1 = (bbb['overid'] <= 8) & (bbb['wickets_lost_before'] >= 3)
p_c1 = np.where(c1, 0.62 + 0.10 * (bbb['wickets_lost_before'] - 3), 0.0)
c2 = (bbb['overid'] <= 12) & (bbb['wickets_lost_before'] >= 4)
p_c2 = np.where(c2, 0.65 + 0.10 * (bbb['wickets_lost_before'] - 4), 0.0)
p_collapse = np.maximum(p_c1, p_c2)

is_death = (bbb['overid'] >= 16)
death_urgency = ((bbb['overid'] - 15) / 5.0).clip(0, 1)
p_death = np.where(is_death, 0.52 + 0.28 * death_urgency, 0.0)
p_death = np.where(is_death & (bbb['wickets_lost_before'] >= 6), np.maximum(p_death, 0.68), p_death)

phase_base = np.where(bbb['overid'] <= 6, 0.20, np.where(bbb['overid'] <= 15, 0.35, 0.60))
wkt_base = (bbb['wickets_lost_before'] / 10.0) * 0.30
pi_inn1_base = phase_base + wkt_base
pi_inn1 = np.maximum(pi_inn1_base, np.maximum(p_collapse, p_death)).clip(0, 1)

pi_raw = np.where(bbb['innings'] == 2, pi_inn2, pi_inn1)
is_playoff = (bbb['knock_out'] == 1) | bbb['stage'].astype(str).str.lower().isin(['final', 'qualifier', 'eliminator', 'semi final', 'super 4'])
stakes_mult = np.where(is_playoff, 1.15, 1.0)
bbb['PI'] = (pi_raw * stakes_mult).clip(0, 1)

print(f"PI range: [{bbb['PI'].min():.3f}, {bbb['PI'].max():.3f}], mean: {bbb['PI'].mean():.3f}")
print(f"Deliveries with PI >= 0.65: {(bbb['PI'] >= 0.65).mean()*100:.2f}% (Target: ~22-25%)")

print("--- 3. TRAINING CONTEXTUAL EXPECTATION MODELS (xRuns & xWicket) ---")
# Feature set
X = pd.DataFrame()
X['innings'] = bbb['innings'].astype('category')
X['overid'] = bbb['overid'].astype(float)
X['over_ball_num'] = bbb['over_ball_num'].astype(float)
X['wickets_lost'] = bbb['wickets_lost_before'].astype(float)
X['pace_or_spin'] = bbb['pace_or_spin'].fillna('Pace').astype('category')
X['venue_id'] = bbb['venue_id'].astype('category')
X['comp_id'] = bbb['comp_id'].astype('category')

# Model 1: xRuns for batters (bat runs)
reg_bat = lgb.LGBMRegressor(n_estimators=100, max_depth=6, learning_rate=0.08, verbose=-1, random_state=42)
reg_bat.fit(X, bbb['runs'].fillna(0))
bbb['xRuns_bat'] = reg_bat.predict(X)

# Model 2: xRuns for bowlers (bowler runs conceded)
reg_bowl = lgb.LGBMRegressor(n_estimators=100, max_depth=6, learning_rate=0.08, verbose=-1, random_state=42)
reg_bowl.fit(X, bbb['bowler_runs_conceded'].fillna(0))
bbb['xRuns_bowl'] = reg_bowl.predict(X)

# Model 3: xWicket for batters (striker out)
clf_bat = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.08, verbose=-1, random_state=42)
clf_bat.fit(X, bbb['is_striker_out'])
bbb['xWkt_bat'] = clf_bat.predict_proba(X)[:, 1]

# Model 4: xWicket for bowlers (bowler wicket)
clf_bowl = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.08, verbose=-1, random_state=42)
clf_bowl.fit(X, bbb['is_bowler_wkt'])
bbb['xWkt_bowl'] = clf_bowl.predict_proba(X)[:, 1]

print("Models trained successfully.")

# Save test checkpoint
bbb[['match_id', 'innings', 'overid', 'striker_id', 'bowler_id', 'PI', 'xRuns_bat', 'xRuns_bowl', 'xWkt_bat', 'xWkt_bowl']].to_feather('temp_bbb_pi.feather')
print("Saved temp_bbb_pi.feather.")

