import pandas as pd
import numpy as np

# Load our cleaned bbb from test_clean_prep logic
bbb = pd.read_csv('6af3166e7b922_data_pack/ball_by_ball.csv', low_memory=False)
mat = pd.read_csv('6af3166e7b922_data_pack/matches.csv', low_memory=False)

bbb = bbb[bbb['innings'].isin([1, 2])].copy()
bbb = bbb.sort_values(['match_id', 'innings', 'innings_ball_num']).reset_index(drop=True)

mat_sub = mat[['match_id', 'comp_id', 'knock_out', 'stage', 'venue_id', 'first_inn_revised_overs', 'second_inn_revised_overs', 'revised_target', 'result']].drop_duplicates('match_id')
bbb = bbb.merge(mat_sub, on='match_id', how='left')
bbb = bbb[bbb['result'].notna()].copy()

bbb['is_batter_legal'] = (bbb['extras_type'] != 'wide').astype(int)
bbb['is_bowler_legal'] = (~bbb['extras_type'].isin(['wide', 'Overstep'])).astype(int)

extra_run = bbb['extras_type'].isin(['wide', 'Overstep', 'legbyes', 'byes', 'other']).astype(int)
penalty_run = (bbb['extras_type'] == 'Penalty').astype(int) * 5
bbb['team_runs_ball'] = bbb['runs'].fillna(0) + bbb['extras_2_runs'].fillna(0) + extra_run + penalty_run

wide_noball = bbb['extras_type'].isin(['wide', 'Overstep']).astype(int)
bbb['bowler_runs_conceded'] = bbb['runs'].fillna(0) + wide_noball + bbb['extras_2_runs'].fillna(0)

bowler_wkt_kinds = ['Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket']
bbb['is_bowler_wkt'] = (bbb['is_wicket'] == True) & (bbb['dismissal_type'].isin(bowler_wkt_kinds))
bbb['is_bowler_wkt'] = bbb['is_bowler_wkt'].astype(int)

# Striker dismissal (exclude non-striker run outs)
striker_out = (bbb['is_wicket'] == True) & (
    (bbb['dismissal_type'] != 'RunOut') | (bbb['dismissed_player_id'] == bbb['striker_id'])
)
bbb['is_striker_out'] = striker_out.astype(int)

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

# ----------------- PRESSURE INDEX CALCULATION -----------------
# 1. Innings 2 Pressure
# Equation pressure: normalized RRR
p_eq = ((bbb['rrr'] - 6.0) / (16.0 - 6.0)).clip(0, 1)

# Resource scarcity: wickets lost vs balls left
res_ratio = ((10.0 - bbb['wickets_lost_before']) / 10.0) * (bbb['balls_remaining'] / bbb['max_overs_balls'].replace(0, 120))
p_scarcity = (1.0 - res_ratio).clip(0, 1)

# Closeness Bell-curve weight: peaks when chase is genuinely contested (RRR in 9-16 with wickets)
# Gaussian bell around RRR=12
closeness_bell = np.exp(-0.5 * ((bbb['rrr'] - 11.5) / 4.0) ** 2)

# Garbage-time dampener:
# Dead win (needing <=6 with >=24 balls and <=4 wickets down)
dead_win = (bbb['runs_required'] <= 6) & (bbb['balls_remaining'] >= 18) & (bbb['wickets_lost_before'] <= 4)
# Impossible loss (needing >=36 off <=6 balls, or >=50 off <=12 balls)
dead_loss = ((bbb['balls_remaining'] <= 6) & (bbb['runs_required'] >= 36)) | \
            ((bbb['balls_remaining'] <= 12) & (bbb['runs_required'] >= 50)) | \
            ((bbb['wickets_lost_before'] >= 9) & (bbb['runs_required'] >= 25) & (bbb['balls_remaining'] <= 12))

closeness_weight = closeness_bell.copy()
closeness_weight = np.where(dead_win, 0.15, closeness_weight)
closeness_weight = np.where(dead_loss, 0.15, closeness_weight)

# Innings 2 raw PI
pi_inn2 = 0.45 * p_eq + 0.35 * p_scarcity + 0.20 * closeness_weight
# If dead win or dead loss, cap at 0.35
pi_inn2 = np.where(dead_win | dead_loss, np.minimum(pi_inn2, 0.35), pi_inn2)

# 2. Innings 1 Pressure
# Early Collapse Rescue
# 3+ wkts inside over 8 (overid <= 8)
c1 = (bbb['overid'] <= 8) & (bbb['wickets_lost_before'] >= 3)
p_c1 = np.where(c1, 0.65 + 0.10 * (bbb['wickets_lost_before'] - 3), 0.0)

# 4+ wkts inside over 12
c2 = (bbb['overid'] <= 12) & (bbb['wickets_lost_before'] >= 4)
p_c2 = np.where(c2, 0.70 + 0.10 * (bbb['wickets_lost_before'] - 4), 0.0)

p_collapse = np.maximum(p_c1, p_c2)

# Death overs acceleration (overs 16-20)
is_death = (bbb['overid'] >= 16)
death_urgency = ((bbb['overid'] - 15) / 5.0).clip(0, 1)
# Death pressure rises as balls tick down, scaled with wickets in hand
p_death = np.where(is_death, 0.60 + 0.25 * death_urgency, 0.0)
# If 8+ wickets lost in 1st innings death, survival is paramount
p_death = np.where(is_death & (bbb['wickets_lost_before'] >= 7), np.maximum(p_death, 0.75), p_death)

# Baseline innings 1 pressure from wickets and phase
phase_base = np.where(bbb['overid'] <= 6, 0.25, np.where(bbb['overid'] <= 15, 0.40, 0.70))
wkt_base = (bbb['wickets_lost_before'] / 10.0) * 0.35
pi_inn1_base = phase_base + wkt_base

pi_inn1 = np.maximum(pi_inn1_base, np.maximum(p_collapse, p_death)).clip(0, 1)

# Combine innings 1 & 2
pi_raw = np.where(bbb['innings'] == 2, pi_inn2, pi_inn1)

# Match Stakes Multiplier: 1.15 if knock_out == 1 or Playoff/Semi/Final
is_playoff = (bbb['knock_out'] == 1) | bbb['stage'].astype(str).str.lower().isin(['final', 'qualifier', 'eliminator', 'semi final', 'super 4'])
stakes_mult = np.where(is_playoff, 1.15, 1.0)

bbb['PI'] = (pi_raw * stakes_mult).clip(0, 1)

print('Pressure Index Summary:')
print(bbb['PI'].describe())

hp_mask = bbb['PI'] >= 0.65
pct_hp = hp_mask.mean() * 100
print(f'\nPercentage of deliveries in High Pressure (PI >= 0.65): {pct_hp:.2f}%')
print(f'Total deliveries: {len(bbb):,}, High Pressure deliveries: {hp_mask.sum():,}')

# Check batter legal balls count per player
hp_bat_counts = bbb[hp_mask & (bbb['is_batter_legal'] == 1)]['striker_id'].value_counts()
print(f'Number of batters with >= 120 legal HP balls: {(hp_bat_counts >= 120).sum()}')
print(f'Number of batters with >= 100 legal HP balls: {(hp_bat_counts >= 100).sum()}')
print('Top 15 batters by HP balls faced:')
print(hp_bat_counts.head(15))

# Check bowler legal balls count per player
hp_bowl_counts = bbb[hp_mask & (bbb['is_bowler_legal'] == 1)]['bowler_id'].value_counts()
print(f'\nNumber of bowlers with >= 120 legal HP balls: {(hp_bowl_counts >= 120).sum()}')
print(f'Number of bowlers with >= 100 legal HP balls: {(hp_bowl_counts >= 100).sum()}')
print('Top 15 bowlers by HP balls bowled:')
print(hp_bowl_counts.head(15))

