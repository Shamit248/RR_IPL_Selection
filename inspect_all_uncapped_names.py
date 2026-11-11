"""
inspect_all_uncapped_names.py
=============================
Inspect all players classified as UNCAPPED to verify 100% that:
1. No overseas players remain.
2. No senior capped India players remain.
"""

import pandas as pd
from classify_all_ipl_players import all_overseas_pids
from audit_capped_by_name import senior_india_capped_names

fit = pd.read_csv('results/player_fit_scores.csv')
comp_map = pd.read_csv('6af3166e7b922_data_pack/competition_team_player_mapping.csv')
status = pd.read_csv('results/player_status.csv')

uncapped_rows = []
for idx, r in fit.iterrows():
    p_id = r['player_id']
    p_name = r['player_name']
    p_name_clean = str(p_name).strip().lower()
    
    if p_id in all_overseas_pids:
        continue
    if p_name_clean in senior_india_capped_names:
        continue
        
    teams = list(comp_map[comp_map['player_id'] == p_id]['team_name'].unique())
    uncapped_rows.append({
        'player_id': p_id,
        'player_name': p_name,
        'teams': teams,
        'rr_squad_2026': r['rr_squad_2026'],
        'first_ipl_season': r['first_ipl_season'],
        'seasons_in_ipl': r['seasons_in_ipl'],
        'RR_FIT_SCORE': r['RR_FIT_SCORE']
    })

df_uncapped = pd.DataFrame(uncapped_rows).sort_values('player_name')
print(f"Total verified UNCAPPED Indian players: {len(df_uncapped)}")

# Save to check
df_uncapped.to_csv('results/temp_uncapped_check.csv', index=False)
for idx, r in df_uncapped.iterrows():
    print(f"{r['player_id']:5d} | {r['player_name']:<30} | RR26: {str(r['rr_squad_2026']):<5} | Teams: {r['teams']}")

