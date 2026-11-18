import pandas as pd
import numpy as np

bbb = pd.read_csv('6af3166e7b922_data_pack/ball_by_ball.csv', low_memory=False)
mat = pd.read_csv('6af3166e7b922_data_pack/matches.csv', low_memory=False)
comps = pd.read_csv('6af3166e7b922_data_pack/competitions.csv', low_memory=False)

# 1. Clean super overs
bbb = bbb[bbb['innings'].isin([1, 2])].copy()

# Sort
bbb = bbb.sort_values(['match_id', 'innings', 'innings_ball_num']).reset_index(drop=True)

# Merge matches
mat_sub = mat[['match_id', 'comp_id', 'knock_out', 'stage', 'venue_id', 'first_inn_revised_overs', 'second_inn_revised_overs', 'revised_target', 'result']].drop_duplicates('match_id')
bbb = bbb.merge(mat_sub, on='match_id', how='left')

# Exclude matches with no result
bbb = bbb[bbb['result'].notna()].copy()

# Legal balls
bbb['is_batter_legal'] = (bbb['extras_type'] != 'wide').astype(int)
bbb['is_bowler_legal'] = (~bbb['extras_type'].isin(['wide', 'Overstep'])).astype(int)

# Runs accounting
extra_run = bbb['extras_type'].isin(['wide', 'Overstep', 'legbyes', 'byes', 'other']).astype(int)
penalty_run = (bbb['extras_type'] == 'Penalty').astype(int) * 5
bbb['team_runs_ball'] = bbb['runs'].fillna(0) + bbb['extras_2_runs'].fillna(0) + extra_run + penalty_run

# Bowler runs conceded = bat runs + wide + noball (legbyes and byes are not bowler's runs!)
wide_noball = bbb['extras_type'].isin(['wide', 'Overstep']).astype(int)
bbb['bowler_runs_conceded'] = bbb['runs'].fillna(0) + wide_noball + bbb['extras_2_runs'].fillna(0)

# Bowler wicket (excludes run outs, retire outs, etc.)
bowler_wkt_kinds = ['Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket']
bbb['is_bowler_wkt'] = (bbb['is_wicket'] == True) & (bbb['dismissal_type'].isin(bowler_wkt_kinds))
bbb['is_bowler_wkt'] = bbb['is_bowler_wkt'].astype(int)

# Cumulative match state
grp = bbb.groupby(['match_id', 'innings'], sort=False)
bbb['score_before'] = grp['team_runs_ball'].transform(lambda s: s.cumsum().shift(1).fillna(0))
bbb['wickets_lost_before'] = grp['is_wicket'].transform(lambda s: s.cumsum().shift(1).fillna(0)).astype(int)
bbb['legal_balls_bowled'] = grp['is_bowler_legal'].transform(lambda s: s.cumsum().shift(1).fillna(0)).astype(int)

# Max balls
bbb['max_overs_balls'] = 120
mask_rev_inn1 = (bbb['innings'] == 1) & bbb['first_inn_revised_overs'].notna() & (bbb['first_inn_revised_overs'] > 0)
bbb.loc[mask_rev_inn1, 'max_overs_balls'] = bbb.loc[mask_rev_inn1, 'first_inn_revised_overs']

mask_rev_inn2 = (bbb['innings'] == 2) & bbb['second_inn_revised_overs'].notna() & (bbb['second_inn_revised_overs'] > 0)
bbb.loc[mask_rev_inn2, 'max_overs_balls'] = bbb.loc[mask_rev_inn2, 'second_inn_revised_overs']

bbb['balls_remaining'] = (bbb['max_overs_balls'] - bbb['legal_balls_bowled']).clip(lower=0)

# Innings 1 totals for targets
inn1_totals = bbb[bbb['innings'] == 1].groupby('match_id')['team_runs_ball'].sum().rename('inn1_total')
bbb = bbb.merge(inn1_totals, on='match_id', how='left')

# Target
bbb['target'] = np.where(bbb['innings'] == 2, bbb['inn1_total'] + 1, np.nan)
mask_rev_target = (bbb['innings'] == 2) & bbb['revised_target'].notna() & (bbb['revised_target'] > 0)
bbb.loc[mask_rev_target, 'target'] = bbb.loc[mask_rev_target, 'revised_target']

bbb['runs_required'] = np.where(bbb['innings'] == 2, (bbb['target'] - bbb['score_before']).clip(lower=0), np.nan)
bbb['rrr'] = np.where(
    (bbb['innings'] == 2) & (bbb['balls_remaining'] > 0),
    (bbb['runs_required'] / bbb['balls_remaining']) * 6.0,
    np.where(bbb['innings'] == 2, 0.0, np.nan)
)

print('Data cleaned. Rows:', len(bbb))
print('Innings 2 sample head:')
print(bbb[bbb['innings'] == 2][['match_id', 'overid', 'score_before', 'wickets_lost_before', 'balls_remaining', 'runs_required', 'rrr']].head(5))

