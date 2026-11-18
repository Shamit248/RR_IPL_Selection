"""
SupeRR Selector Season 2 (Round 1) — High-Pressure T20 Player Rating Engine
=============================================================================
Reproducible, quantitative player evaluation system built for the Rajasthan Royals
SupeRR Selector challenge.

Ingests 6 CSV datasets (IPL & T20I data from 2022 onwards), models delivery-level
contextual Pressure Index (PI), trains LightGBM contextual expectation models
(xRuns & xWicket), and ranks the Top 10 Batters and Top 10 Bowlers under pressure.
"""

import os
import sys
import time
import warnings
import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.stats import spearmanr

warnings.filterwarnings('ignore')

DATA_DIR = '6af3166e7b922_data_pack'
OUT_DIR  = 'results'
os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 80)
print("SupeRR SELECTOR SEASON 2 (ROUND 1) — HIGH-PRESSURE T20 PLAYER RATING ENGINE")
print("=" * 80)

# =============================================================================
# 1. INPUT SCHEMA & JOINS
# =============================================================================
print("\n[STEP 1] Loading raw datasets...")
t0 = time.time()
bbb   = pd.read_csv(os.path.join(DATA_DIR, 'ball_by_ball.csv'), low_memory=False)
mat   = pd.read_csv(os.path.join(DATA_DIR, 'matches.csv'), low_memory=False)
comps = pd.read_csv(os.path.join(DATA_DIR, 'competitions.csv'), low_memory=False)
teams = pd.read_csv(os.path.join(DATA_DIR, 'teams.csv'), low_memory=False)
pe    = pd.read_csv(os.path.join(DATA_DIR, 'playing_eleven.csv'), low_memory=False)
cmap  = pd.read_csv(os.path.join(DATA_DIR, 'competition_team_player_mapping.csv'), low_memory=False)

print(f"  Loaded ball_by_ball.csv: {len(bbb):,} rows")
print(f"  Loaded matches.csv: {len(mat):,} rows")
print(f"  Loaded competitions.csv: {len(comps):,} rows")
print(f"  Loaded teams.csv: {len(teams):,} rows")
print(f"  Loaded playing_eleven.csv: {len(pe):,} rows")
print(f"  Loaded competition_team_player_mapping.csv: {len(cmap):,} rows")

# Build unified player name dictionary
player_name_map = cmap.drop_duplicates('player_id').set_index('player_id')['player_name'].to_dict()
bbb['striker_name'] = bbb['striker_id'].map(player_name_map).fillna(bbb['striker_name'])
bbb['bowler_name']  = bbb['bowler_id'].map(player_name_map).fillna(bbb['bowler_name'])

# Latest team map
player_team_map = cmap.sort_values('comp_id', ascending=False).drop_duplicates('player_id').set_index('player_id')['team_name'].to_dict()

# =============================================================================
# 2. DATA CLEANING & MATCH STATE RECONSTRUCTION
# =============================================================================
print("\n[STEP 2] Cleaning data and reconstructing match states...")

# Filter Super Overs (keep standard innings 1 & 2)
bbb = bbb[bbb['innings'].isin([1, 2])].copy()

# Sort chronologically
bbb = bbb.sort_values(['match_id', 'innings', 'innings_ball_num']).reset_index(drop=True)

# Merge match metadata
mat_cols = [
    'match_id', 'comp_id', 'match_number', 'match_date', 'stage', 'venue_id',
    'venue_country', 'home_team_id', 'away_team_id', 'knock_out', 'win_team_id',
    'result', 'first_inn_revised_overs', 'second_inn_revised_overs', 'revised_target'
]
mat_sub = mat[[c for c in mat_cols if c in mat.columns]].drop_duplicates('match_id')
bbb = bbb.merge(mat_sub, on='match_id', how='left')

# Exclude abandoned / no-result matches
bbb = bbb[bbb['result'].notna()].copy()
print(f"  Deliveries after filtering abandoned matches: {len(bbb):,}")

# Legal deliveries:
# Batter legal ball faced: extras_type != 'wide' (noballs count as faced)
bbb['is_batter_legal'] = (bbb['extras_type'] != 'wide').astype(int)

# Bowler legal ball bowled: extras_type not in ['wide', 'Overstep']
bbb['is_bowler_legal'] = (~bbb['extras_type'].isin(['wide', 'Overstep'])).astype(int)

# Runs accounting:
# extras1_runs in raw dataset is encoded categorical ID (1=noball, 2=wide, etc.).
# Team extras per ball: 1 for wide/noball/bye/legbye, 5 for penalty
extra_run = bbb['extras_type'].isin(['wide', 'Overstep', 'legbyes', 'byes', 'other']).astype(int)
penalty_run = (bbb['extras_type'] == 'Penalty').astype(int) * 5
bbb['team_runs_ball'] = bbb['runs'].fillna(0) + bbb['extras_2_runs'].fillna(0) + extra_run + penalty_run

# Bowler runs conceded: bat runs + wide extras + noball extras (byes and legbyes are not bowler's runs)
wide_noball = bbb['extras_type'].isin(['wide', 'Overstep']).astype(int)
bbb['bowler_runs_conceded'] = bbb['runs'].fillna(0) + wide_noball + bbb['extras_2_runs'].fillna(0)

# Bowler wickets (excludes runouts, retired out, etc.)
bowler_wkt_kinds = ['Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket']
bbb['is_bowler_wkt'] = (bbb['is_wicket'] == True) & (bbb['dismissal_type'].isin(bowler_wkt_kinds))
bbb['is_bowler_wkt'] = bbb['is_bowler_wkt'].astype(int)

# Striker dismissal (excludes non-striker runouts)
striker_out = (bbb['is_wicket'] == True) & (
    (bbb['dismissal_type'] != 'RunOut') | (bbb['dismissed_player_id'] == bbb['striker_id'])
)
bbb['is_striker_out'] = striker_out.astype(int)

# Cumulative match state
grp = bbb.groupby(['match_id', 'innings'], sort=False)
bbb['score_before'] = grp['team_runs_ball'].transform(lambda s: s.cumsum().shift(1).fillna(0))
bbb['wickets_lost_before'] = grp['is_wicket'].transform(lambda s: s.cumsum().shift(1).fillna(0)).astype(int)
bbb['legal_balls_bowled'] = grp['is_bowler_legal'].transform(lambda s: s.cumsum().shift(1).fillna(0)).astype(int)

# D/L revised overs handling (values are stored in balls)
bbb['max_overs_balls'] = 120
mask_rev_inn1 = (bbb['innings'] == 1) & bbb['first_inn_revised_overs'].notna() & (bbb['first_inn_revised_overs'] > 0)
bbb.loc[mask_rev_inn1, 'max_overs_balls'] = bbb.loc[mask_rev_inn1, 'first_inn_revised_overs']

mask_rev_inn2 = (bbb['innings'] == 2) & bbb['second_inn_revised_overs'].notna() & (bbb['second_inn_revised_overs'] > 0)
bbb.loc[mask_rev_inn2, 'max_overs_balls'] = bbb.loc[mask_rev_inn2, 'second_inn_revised_overs']

bbb['balls_remaining'] = (bbb['max_overs_balls'] - bbb['legal_balls_bowled']).clip(lower=0)

# Innings 2 Target & RRR
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

# =============================================================================
# 3. PRESSURE INDEX (PI) ENGINEERING
# =============================================================================
print("\n[STEP 3] Engineering continuous delivery-level Pressure Index (PI)...")

# --- Innings 2 (Chasing) ---
# Equation Pressure
p_eq = ((bbb['rrr'] - 6.5) / (16.5 - 6.5)).clip(0, 1)

# Resource Scarcity
res_ratio = ((10.0 - bbb['wickets_lost_before']) / 10.0) * (bbb['balls_remaining'] / bbb['max_overs_balls'].replace(0, 120))
p_scarcity = (1.0 - res_ratio).clip(0, 1)

# Closeness Bell-Curve Weight: peaks when genuinely contested (RRR around 11.5 with wickets)
closeness_bell = np.exp(-0.5 * ((bbb['rrr'] - 11.5) / 4.0) ** 2)

# Garbage-time identification (dead games)
dead_win = (bbb['runs_required'] <= 6) & (bbb['balls_remaining'] >= 18) & (bbb['wickets_lost_before'] <= 4)
dead_loss = ((bbb['balls_remaining'] <= 6) & (bbb['runs_required'] >= 36)) | \
            ((bbb['balls_remaining'] <= 12) & (bbb['runs_required'] >= 48)) | \
            ((bbb['wickets_lost_before'] >= 9) & (bbb['runs_required'] >= 24) & (bbb['balls_remaining'] <= 12))

closeness_weight = closeness_bell.copy()
closeness_weight = np.where(dead_win | dead_loss, 0.10, closeness_weight)

pi_inn2 = 0.45 * p_eq + 0.35 * p_scarcity + 0.20 * closeness_weight
pi_inn2 = np.where(dead_win | dead_loss, np.minimum(pi_inn2, 0.30), pi_inn2)

# --- Innings 1 (Target Setting) ---
# Collapse rescue
c1 = (bbb['overid'] <= 8) & (bbb['wickets_lost_before'] >= 3)
p_c1 = np.where(c1, 0.62 + 0.10 * (bbb['wickets_lost_before'] - 3), 0.0)

c2 = (bbb['overid'] <= 12) & (bbb['wickets_lost_before'] >= 4)
p_c2 = np.where(c2, 0.65 + 0.10 * (bbb['wickets_lost_before'] - 4), 0.0)
p_collapse = np.maximum(p_c1, p_c2)

# Death overs acceleration (overs 16-20)
is_death = (bbb['overid'] >= 16)
death_urgency = ((bbb['overid'] - 15) / 5.0).clip(0, 1)
p_death = np.where(is_death, 0.52 + 0.28 * death_urgency, 0.0)
p_death = np.where(is_death & (bbb['wickets_lost_before'] >= 6), np.maximum(p_death, 0.68), p_death)

phase_base = np.where(bbb['overid'] <= 6, 0.20, np.where(bbb['overid'] <= 15, 0.35, 0.60))
wkt_base = (bbb['wickets_lost_before'] / 10.0) * 0.30
pi_inn1_base = phase_base + wkt_base
pi_inn1 = np.maximum(pi_inn1_base, np.maximum(p_collapse, p_death)).clip(0, 1)

pi_raw = np.where(bbb['innings'] == 2, pi_inn2, pi_inn1)

# Match stakes multiplier: 1.15 in playoffs/knockouts
is_playoff = (bbb['knock_out'] == 1) | bbb['stage'].astype(str).str.lower().isin(
    ['final', 'qualifier', 'eliminator', 'semi final', 'super 4']
)
stakes_mult = np.where(is_playoff, 1.15, 1.0)
bbb['PI'] = (pi_raw * stakes_mult).clip(0, 1)

hp_mask = bbb['PI'] >= 0.65
pct_hp = hp_mask.mean() * 100
print(f"  Delivery Pressure Index calibrated: range [{bbb['PI'].min():.3f}, {bbb['PI'].max():.3f}], mean: {bbb['PI'].mean():.3f}")
print(f"  High-Pressure Deliveries (PI >= 0.65): {hp_mask.sum():,} ({pct_hp:.2f}% of dataset)")

# =============================================================================
# 4. CONTEXTUAL EXPECTED OUTCOME MODELS (xRuns & xWicket)
# =============================================================================
print("\n[STEP 4] Training LightGBM expected outcome baseline models...")
X = pd.DataFrame()
X['innings'] = bbb['innings'].astype('category')
X['overid'] = bbb['overid'].astype(float)
X['over_ball_num'] = bbb['over_ball_num'].astype(float)
X['wickets_lost'] = bbb['wickets_lost_before'].astype(float)
X['pace_or_spin'] = bbb['pace_or_spin'].fillna('Pace').astype('category')
X['venue_id'] = bbb['venue_id'].astype('category')
X['comp_id'] = bbb['comp_id'].astype('category')

# xRuns for batters (bat runs)
reg_bat = lgb.LGBMRegressor(n_estimators=100, max_depth=6, learning_rate=0.08, verbose=-1, random_state=42)
reg_bat.fit(X, bbb['runs'].fillna(0))
bbb['xRuns_bat'] = reg_bat.predict(X)

# xRuns for bowlers (bowler runs conceded)
reg_bowl = lgb.LGBMRegressor(n_estimators=100, max_depth=6, learning_rate=0.08, verbose=-1, random_state=42)
reg_bowl.fit(X, bbb['bowler_runs_conceded'].fillna(0))
bbb['xRuns_bowl'] = reg_bowl.predict(X)

# xWicket for batters
clf_bat = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.08, verbose=-1, random_state=42)
clf_bat.fit(X, bbb['is_striker_out'])
bbb['xWkt_bat'] = clf_bat.predict_proba(X)[:, 1]

# xWicket for bowlers
clf_bowl = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.08, verbose=-1, random_state=42)
clf_bowl.fit(X, bbb['is_bowler_wkt'])
bbb['xWkt_bowl'] = clf_bowl.predict_proba(X)[:, 1]

print("  Models trained successfully:")
print(f"    Batter xRuns mean = {bbb['xRuns_bat'].mean():.3f} vs actual = {bbb['runs'].mean():.3f}")
print(f"    Bowler xRuns mean = {bbb['xRuns_bowl'].mean():.3f} vs actual = {bbb['bowler_runs_conceded'].mean():.3f}")
print(f"    Wicket xProb mean = {bbb['xWkt_bowl'].mean():.4f} vs actual = {bbb['is_bowler_wkt'].mean():.4f}")

# =============================================================================
# 5. PRESSURE DEFINITION PROOF
# =============================================================================
print("\n[STEP 5] Generating Pressure Definition Proof table...")
proof_rows = []
for label, mask in [('Normal / Baseline Zone (PI < 0.65)', ~hp_mask), ('High-Pressure Zone (PI >= 0.65)', hp_mask)]:
    sub = bbb[mask]
    n_balls = len(sub)
    legal_balls = sub['is_bowler_legal'].sum()
    runs_total = sub['team_runs_ball'].sum()
    wickets_total = sub['is_wicket'].sum()
    econ = (runs_total / (legal_balls / 6.0)) if legal_balls > 0 else 0
    wkt_rate = (wickets_total / (legal_balls / 6.0)) if legal_balls > 0 else 0
    dot_pct = ((sub['team_runs_ball'] == 0).sum() / n_balls) * 100.0
    bnd_pct = (sub['is_boundary'].sum() / n_balls) * 100.0 if 'is_boundary' in sub.columns else (((sub['is_four'] == True) | (sub['is_six'] == True)).sum() / n_balls) * 100.0
    proof_rows.append({
        'Pressure_Zone': label,
        'Deliveries': n_balls,
        'Pct_of_Dataset': round((n_balls / len(bbb)) * 100.0, 2),
        'Scoring_Economy': round(econ, 2),
        'Wickets_Per_Over': round(wkt_rate, 3),
        'Dot_Ball_Pct': round(dot_pct, 2),
        'Boundary_Pct': round(bnd_pct, 2)
    })

proof_df = pd.DataFrame(proof_rows)
proof_path = os.path.join(OUT_DIR, 'pressure_definition_proof.csv')
proof_df.to_csv(proof_path, index=False)
print(f"  Saved {proof_path}:")
print(proof_df.to_string(index=False))

# =============================================================================
# 6. BATTER PRESSURE PERFORMANCE & RANKINGS
# =============================================================================
print("\n[STEP 6] Computing Batter Clutch Rating across entire dataset...")
bat_legal = bbb[bbb['is_batter_legal'] == 1].copy()
hp_mask_bat = hp_mask.loc[bat_legal.index]

hp_bat = bat_legal[hp_mask_bat].groupby('striker_id').agg(
    player_name=('striker_name', 'first'),
    hp_matches=('match_id', 'nunique'),
    hp_balls=('is_batter_legal', 'sum'),
    hp_runs=('runs', 'sum'),
    hp_xruns=('xRuns_bat', 'sum'),
    hp_outs=('is_striker_out', 'sum'),
    hp_xwkt=('xWkt_bat', 'sum'),
    hp_fours=('is_four', lambda s: (s == True).sum()),
    hp_sixes=('is_six', lambda s: (s == True).sum()),
    hp_dots=('runs', lambda s: (s == 0).sum())
).reset_index()

us_bat = bat_legal[~hp_mask_bat].groupby('striker_id').agg(
    us_matches=('match_id', 'nunique'),
    us_balls=('is_batter_legal', 'sum'),
    us_runs=('runs', 'sum'),
    us_outs=('is_striker_out', 'sum')
).reset_index()

bat_df = hp_bat.merge(us_bat, on='striker_id', how='left')
tot_matches_bat = bat_legal.groupby('striker_id')['match_id'].nunique().rename('total_matches')
bat_df = bat_df.merge(tot_matches_bat, on='striker_id', how='left')

# Rates
bat_df['Pressure_SR'] = (bat_df['hp_runs'] / bat_df['hp_balls']) * 100.0
bat_df['Usual_SR'] = np.where(bat_df['us_balls'] >= 20, (bat_df['us_runs'] / bat_df['us_balls']) * 100.0, np.nan)
bat_df['Delta_SR'] = bat_df['Pressure_SR'] - bat_df['Usual_SR']
bat_df['Raw_RAA_100'] = ((bat_df['hp_runs'] - bat_df['hp_xruns']) / bat_df['hp_balls']) * 100.0
bat_df['Pressure_Boundary_Pct'] = ((bat_df['hp_fours'] + bat_df['hp_sixes']) / bat_df['hp_balls']) * 100.0
bat_df['Pressure_Dot_Pct'] = (bat_df['hp_dots'] / bat_df['hp_balls']) * 100.0
bat_df['Wicket_Preservation'] = bat_df['hp_xwkt'] / bat_df['hp_outs'].clip(lower=1)

# Consistency Score
hp_match_bat = bat_legal[hp_mask_bat].groupby(['striker_id', 'match_id']).agg(
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
print(f"  Qualified Batters (>= 120 legal HP balls): {len(bat_120)}")

# Empirical Bayes Shrinkage
mu_bat_raa = bat_120['Raw_RAA_100'].mean()
K_bat = 40.0
bat_120['shrink_w'] = bat_120['hp_balls'] / (bat_120['hp_balls'] + K_bat)
bat_120['Pressure_RAA_100'] = bat_120['shrink_w'] * bat_120['Raw_RAA_100'] + (1 - bat_120['shrink_w']) * mu_bat_raa

def min_max_norm(s, clip_q=(0.02, 0.98)):
    lo, hi = s.quantile(clip_q[0]), s.quantile(clip_q[1])
    if hi == lo: return pd.Series(50.0, index=s.index)
    return ((s.clip(lo, hi) - lo) / (hi - lo) * 100.0).clip(0, 100)

s_raa = min_max_norm(bat_120['Pressure_RAA_100'])
s_dsr = min_max_norm(bat_120['Delta_SR'].fillna(0))
s_cons = min_max_norm(bat_120['Consistency_Pct'])
s_wp = min_max_norm(bat_120['Wicket_Preservation'].clip(upper=3.0))

bat_120['Final_Clutch_Index'] = (0.40 * s_raa + 0.25 * s_dsr + 0.20 * s_cons + 0.15 * s_wp).round(2)
bat_ranked = bat_120.sort_values('Final_Clutch_Index', ascending=False).reset_index(drop=True)
bat_ranked['rank'] = range(1, len(bat_ranked) + 1)
bat_ranked['team_name'] = bat_ranked['striker_id'].map(player_team_map).fillna('International / Franchise')

# =============================================================================
# 7. BOWLER PRESSURE PERFORMANCE & RANKINGS
# =============================================================================
print("\n[STEP 7] Computing Bowler Clutch Rating across entire dataset...")
bowl_legal = bbb[bbb['is_bowler_legal'] == 1].copy()
hp_mask_bowl = hp_mask.loc[bowl_legal.index]

hp_bowl = bowl_legal[hp_mask_bowl].groupby('bowler_id').agg(
    player_name=('bowler_name', 'first'),
    hp_matches=('match_id', 'nunique'),
    hp_balls=('is_bowler_legal', 'sum'),
    hp_runs_conceded=('bowler_runs_conceded', 'sum'),
    hp_xruns=('xRuns_bowl', 'sum'),
    hp_wkts=('is_bowler_wkt', 'sum'),
    hp_xwkt=('xWkt_bowl', 'sum'),
    hp_dots=('bowler_runs_conceded', lambda s: (s == 0).sum()),
    hp_fours=('is_four', lambda s: (s == True).sum()),
    hp_sixes=('is_six', lambda s: (s == True).sum())
).reset_index()

us_bowl = bowl_legal[~hp_mask_bowl].groupby('bowler_id').agg(
    us_matches=('match_id', 'nunique'),
    us_balls=('is_bowler_legal', 'sum'),
    us_runs_conceded=('bowler_runs_conceded', 'sum'),
    us_wkts=('is_bowler_wkt', 'sum')
).reset_index()

bowl_df = hp_bowl.merge(us_bowl, on='bowler_id', how='left')
tot_matches_bowl = bowl_legal.groupby('bowler_id')['match_id'].nunique().rename('total_matches')
bowl_df = bowl_df.merge(tot_matches_bowl, on='bowler_id', how='left')

# Rates
bowl_df['Pressure_Econ'] = (bowl_df['hp_runs_conceded'] / (bowl_df['hp_balls'] / 6.0))
bowl_df['Usual_Econ'] = np.where(bowl_df['us_balls'] >= 24, (bowl_df['us_runs_conceded'] / (bowl_df['us_balls'] / 6.0)), np.nan)
bowl_df['Delta_Econ'] = bowl_df['Usual_Econ'] - bowl_df['Pressure_Econ']
bowl_df['Raw_RSAE_24'] = ((bowl_df['hp_xruns'] - bowl_df['hp_runs_conceded']) / bowl_df['hp_balls']) * 24.0
bowl_df['Wickets_Above_Exp'] = bowl_df['hp_wkts'] - bowl_df['hp_xwkt']
bowl_df['Pressure_Dot_Pct'] = (bowl_df['hp_dots'] / bowl_df['hp_balls']) * 100.0
bowl_df['Pressure_Boundary_Conceded_Pct'] = ((bowl_df['hp_fours'] + bowl_df['hp_sixes']) / bowl_df['hp_balls']) * 100.0

# Consistency Score
hp_match_bowl = bowl_legal[hp_mask_bowl].groupby(['bowler_id', 'match_id']).agg(
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
print(f"  Qualified Bowlers (>= 120 legal HP balls): {len(bowl_120)}")

# Empirical Bayes Shrinkage
mu_bowl_rsae = bowl_120['Raw_RSAE_24'].mean()
K_bowl = 40.0
bowl_120['shrink_w'] = bowl_120['hp_balls'] / (bowl_120['hp_balls'] + K_bowl)
bowl_120['Pressure_RSAE_24'] = bowl_120['shrink_w'] * bowl_120['Raw_RSAE_24'] + (1 - bowl_120['shrink_w']) * mu_bowl_rsae

s_rsae = min_max_norm(bowl_120['Pressure_RSAE_24'])
s_decon = min_max_norm(bowl_120['Delta_Econ'].fillna(0))
s_bcons = min_max_norm(bowl_120['Consistency_Pct'])
s_wae = min_max_norm(bowl_120['Wickets_Above_Exp'].clip(lower=-5, upper=15))

bowl_120['Final_Clutch_Index'] = (0.40 * s_rsae + 0.25 * s_decon + 0.20 * s_bcons + 0.15 * s_wae).round(2)
bowl_ranked = bowl_120.sort_values('Final_Clutch_Index', ascending=False).reset_index(drop=True)
bowl_ranked['rank'] = range(1, len(bowl_ranked) + 1)
bowl_ranked['team_name'] = bowl_ranked['bowler_id'].map(player_team_map).fillna('International / Franchise')

# =============================================================================
# 8. SAVE REQUIRED OUTPUT CSVS
# =============================================================================
print("\n[STEP 8] Saving Top 10, Top 25, and Sensitivity Analysis CSVs...")

# Top 10 Batters
bat_top10_cols = [
    'rank', 'striker_id', 'player_name', 'team_name', 'total_matches', 'hp_balls',
    'Usual_SR', 'Pressure_SR', 'Delta_SR', 'Pressure_RAA_100', 'Consistency_Pct', 'Final_Clutch_Index'
]
bat_top10 = bat_ranked[bat_top10_cols].head(10).rename(columns={'striker_id': 'player_id'})
bat_top10_path = os.path.join(OUT_DIR, 'top10_pressure_batters.csv')
bat_top10.to_csv(bat_top10_path, index=False)

# Top 25 Batters
bat_top25 = bat_ranked[bat_top10_cols].head(25).rename(columns={'striker_id': 'player_id'})
bat_top25_path = os.path.join(OUT_DIR, 'top25_pressure_batters.csv')
bat_top25.to_csv(bat_top25_path, index=False)

# Top 10 Bowlers
bowl_top10_cols = [
    'rank', 'bowler_id', 'player_name', 'team_name', 'total_matches', 'hp_balls',
    'Usual_Econ', 'Pressure_Econ', 'Delta_Econ', 'Pressure_RSAE_24', 'Wickets_Above_Exp', 'Consistency_Pct', 'Final_Clutch_Index'
]
bowl_top10 = bowl_ranked[bowl_top10_cols].head(10).rename(columns={'bowler_id': 'player_id'})
bowl_top10_path = os.path.join(OUT_DIR, 'top10_pressure_bowlers.csv')
bowl_top10.to_csv(bowl_top10_path, index=False)

# Top 25 Bowlers
bowl_top25 = bowl_ranked[bowl_top10_cols].head(25).rename(columns={'bowler_id': 'player_id'})
bowl_top25_path = os.path.join(OUT_DIR, 'top25_pressure_bowlers.csv')
bowl_top25.to_csv(bowl_top25_path, index=False)

# =============================================================================
# 9. SENSITIVITY ANALYSIS
# =============================================================================
print("\n[STEP 9] Running Spearman sensitivity analysis across PI cutoffs & sample thresholds...")

def get_sensitivity_rankings(is_bat=True, pi_thresh=0.65, min_balls=120):
    hp_m = bbb['PI'] >= pi_thresh
    if is_bat:
        sub = bbb[bbb['is_batter_legal'] == 1]
        hp = sub[hp_m.loc[sub.index]].groupby('striker_id').agg(
            hp_balls=('is_batter_legal', 'sum'),
            hp_runs=('runs', 'sum'),
            hp_xruns=('xRuns_bat', 'sum')
        ).reset_index()
        us = sub[~hp_m.loc[sub.index]].groupby('striker_id').agg(
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
        m['shrunk_raa'] = w * m['Raw_RAA_100'] + (1 - w) * mu
        s1 = min_max_norm(m['shrunk_raa'])
        s2 = min_max_norm(m['Delta_SR'].fillna(0))
        m['score'] = 0.6 * s1 + 0.4 * s2
        return m.sort_values('score', ascending=False).set_index('striker_id')['score']
    else:
        sub = bbb[bbb['is_bowler_legal'] == 1]
        hp = sub[hp_m.loc[sub.index]].groupby('bowler_id').agg(
            hp_balls=('is_bowler_legal', 'sum'),
            hp_runs=('bowler_runs_conceded', 'sum'),
            hp_xruns=('xRuns_bowl', 'sum')
        ).reset_index()
        us = sub[~hp_m.loc[sub.index]].groupby('bowler_id').agg(
            us_balls=('is_bowler_legal', 'sum'),
            us_runs=('bowler_runs_conceded', 'sum')
        ).reset_index()
        m = hp.merge(us, on='bowler_id', how='left')
        m = m[m['hp_balls'] >= min_balls].copy()
        m['Pressure_Econ'] = (m['hp_runs'] / (m['hp_balls'] / 6.0))
        m['Usual_Econ'] = (m['us_runs'] / (m['us_balls'].clip(lower=1) / 6.0))
        m['Delta_Econ'] = m['Usual_Econ'] - m['Pressure_Econ']
        m['Raw_RSAE_24'] = ((m['hp_xruns'] - m['hp_runs']) / m['hp_balls']) * 24.0
        mu = m['Raw_RSAE_24'].mean()
        w = m['hp_balls'] / (m['hp_balls'] + 40.0)
        m['shrunk_rsae'] = w * m['Raw_RSAE_24'] + (1 - w) * mu
        s1 = min_max_norm(m['shrunk_rsae'])
        s2 = min_max_norm(m['Delta_Econ'].fillna(0))
        m['score'] = 0.6 * s1 + 0.4 * s2
        return m.sort_values('score', ascending=False).set_index('bowler_id')['score']

sens_rows = []
base_bat_scores = get_sensitivity_rankings(True, 0.65, 120)
base_bowl_scores = get_sensitivity_rankings(False, 0.65, 120)

for p in [0.60, 0.65, 0.70]:
    for b in [100, 120, 150]:
        alt_bat = get_sensitivity_rankings(True, p, b)
        c_bat = base_bat_scores.index.intersection(alt_bat.index)
        rho_bat, _ = spearmanr(base_bat_scores.loc[c_bat], alt_bat.loc[c_bat])
        
        alt_bowl = get_sensitivity_rankings(False, p, b)
        c_bowl = base_bowl_scores.index.intersection(alt_bowl.index)
        rho_bowl, _ = spearmanr(base_bowl_scores.loc[c_bowl], alt_bowl.loc[c_bowl])
        
        sens_rows.append({
            'PI_Cutoff': p,
            'Min_Balls_Threshold': b,
            'Batters_Evaluated': len(c_bat),
            'Batting_Spearman_Rho': round(rho_bat, 3),
            'Bowlers_Evaluated': len(c_bowl),
            'Bowling_Spearman_Rho': round(rho_bowl, 3)
        })

sens_df = pd.DataFrame(sens_rows)
sens_path = os.path.join(OUT_DIR, 'sensitivity_analysis.csv')
sens_df.to_csv(sens_path, index=False)
print(f"  Saved {sens_path}:")
print(sens_df.to_string(index=False))

# =============================================================================
# 10. DISPLAY OFFICIAL TOP 10 RANKINGS
# =============================================================================
print("\n" + "=" * 80)
print("OFFICIAL TOP 10 BATTERS UNDER PRESSURE (SupeRR Selector Season 2)")
print("=" * 80)
print(bat_top10.to_string(index=False))

print("\n" + "=" * 80)
print("OFFICIAL TOP 10 BOWLERS UNDER PRESSURE (SupeRR Selector Season 2)")
print("=" * 80)
print(bowl_top10.to_string(index=False))

print("\n" + "#" * 80)
print("PIPELINE COMPLETED SUCCESSFULLY! All deliverables saved in 'results/'.")
print("#" * 80)

