import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
comps = pd.read_csv(f'{DATA_DIR}/competitions.csv')
pe = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')
matches = pd.read_csv(f'{DATA_DIR}/matches.csv')

pe_m = pe.merge(matches[['match_id', 'comp_id', 'match_date']], on='match_id', how='left')
pe_m = pe_m.merge(comps[['comp_id', 'comp_name', 'match_format', 'season']], on='comp_id', how='left')

ipl_comps = {1358: 2022, 1715: 2023, 2193: 2024, 2725: 2025, 3298: 2026}
ipl_cm = comp_map[comp_map['comp_id'].isin(ipl_comps.keys())].copy()
ipl_cm['season'] = ipl_cm['comp_id'].map(ipl_comps)

player_last = ipl_cm.groupby(['player_id', 'player_name']).agg(
    last_ipl_squad=('season', 'max')
).reset_index()

# Last match in any competition in our dataset
last_match_any = pe_m[pe_m['is_played'] == True].groupby('player_id').agg(
    last_match_date=('match_date', 'max'),
    last_match_comp=('comp_name', 'last'),
    last_match_season=('season', 'max')
).reset_index()

player_last = player_last.merge(last_match_any, on='player_id', how='left')

# Last IPL played
pe_ipl = pe_m[(pe_m['comp_id'].isin(ipl_comps.keys())) & (pe_m['is_played'] == True)]
last_ipl_p = pe_ipl.groupby('player_id')['season'].max().reset_index().rename(columns={'season': 'last_ipl_played'})
player_last = player_last.merge(last_ipl_p, on='player_id', how='left')

# Filter absent in 2026 squad
absent = player_last[player_last['last_ipl_squad'] < 2026].sort_values(['last_ipl_squad', 'player_name'])

print(f"Total absent from 2026 squad: {len(absent)}")
print("\nBreakdown by last IPL squad season:")
print(absent['last_ipl_squad'].value_counts().sort_index())
