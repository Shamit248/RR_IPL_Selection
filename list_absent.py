import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
comps = pd.read_csv(f'{DATA_DIR}/competitions.csv')
ipl_comps = {1358: 2022, 1715: 2023, 2193: 2024, 2725: 2025, 3298: 2026}
ipl_cm = comp_map[comp_map['comp_id'].isin(ipl_comps.keys())].copy()
ipl_cm['season'] = ipl_cm['comp_id'].map(ipl_comps)

player_info = ipl_cm.groupby(['player_id', 'player_name']).agg(
    last_ipl_squad=('season', 'max')
).reset_index()

not_in_2026 = player_info[player_info['last_ipl_squad'] < 2026].sort_values('player_name')

print("All 202 players not in 2026 squad:")
for i, (idx, r) in enumerate(not_in_2026.iterrows()):
    print(f"{r['player_id']}: {r['player_name']} ({r['last_ipl_squad']})", end=", ")
    if (i+1) % 4 == 0:
        print()
print()
