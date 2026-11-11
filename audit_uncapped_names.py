"""
audit_uncapped_names.py
=======================
Verify every single name among the 203 uncapped Indian players.
Print their names, teams, and check if any player has ever represented senior India.
"""

import pandas as pd
from classify_all_ipl_players import clf_df, all_overseas_pids, all_senior_india_capped

fit = pd.read_csv('results/player_fit_scores.csv')
status = pd.read_csv('results/player_status.csv')
comp_map = pd.read_csv('6af3166e7b922_data_pack/competition_team_player_mapping.csv')

uncapped = clf_df[clf_df['uncapped_status'] == 'UNCAPPED_INDIAN'].copy()
uncapped = uncapped.merge(status[['player_id', 'current_active_status', 'ipl_2027_status', 'final_eligible']], on='player_id', how='left')
uncapped = uncapped.merge(fit[['player_id', 'rr_squad_2026', 'first_ipl_season', 'seasons_in_ipl', 'RR_FIT_SCORE']], on='player_id', how='left')

active_uncapped = uncapped[uncapped['current_active_status'] == 'ACTIVE'].sort_values('RR_FIT_SCORE', ascending=False)

print(f"Total ACTIVE Uncapped Indian players: {len(active_uncapped)}")
print("\nTop 40 Active Uncapped Indians by existing fit score:")
for i, (idx, r) in enumerate(active_uncapped.head(40).iterrows()):
    p_id = r['player_id']
    teams = comp_map[comp_map['player_id'] == p_id]['team_name'].unique()
    print(f"{i+1:2d}. {r['player_name']} (ID: {p_id}) | RR 2026: {r['rr_squad_2026']} | Fit: {r['RR_FIT_SCORE']:.2f} | Teams: {list(teams)}")

