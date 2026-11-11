import pandas as pd

DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
comps = pd.read_csv(f'{DATA_DIR}/competitions.csv')
ipl_comps = {1358: 2022, 1715: 2023, 2193: 2024, 2725: 2025, 3298: 2026}

ipl_cm = comp_map[comp_map['comp_id'].isin(ipl_comps.keys())].copy()
ipl_cm['season'] = ipl_cm['comp_id'].map(ipl_comps)

# Player name and ID mapping
player_info = ipl_cm.groupby(['player_id', 'player_name']).agg(
    last_ipl_squad_season=('season', 'max'),
    ipl_seasons_squad=('season', lambda s: sorted(list(set(s))))
).reset_index()

# Check playing eleven
pe = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')
matches = pd.read_csv(f'{DATA_DIR}/matches.csv')
pe_m = pe.merge(matches[['match_id', 'comp_id']], on='match_id', how='left')
pe_ipl = pe_m[(pe_m['comp_id'].isin(ipl_comps.keys())) & (pe_m['is_played'] == True)].copy()
pe_ipl['season'] = pe_ipl['comp_id'].map(ipl_comps)

last_played = pe_ipl.groupby('player_id')['season'].max().reset_index().rename(columns={'season': 'last_ipl_played_season'})
player_info = player_info.merge(last_played, on='player_id', how='left')

# Check T20I appearances
t20i_comps = comps[comps['match_format'] == 'T20I']['comp_id'].unique()
pe_t20i = pe_m[(pe_m['comp_id'].isin(t20i_comps)) & (pe_m['is_played'] == True)].copy()
pe_t20i = pe_t20i.merge(comps[['comp_id', 'season']], on='comp_id', how='left')
last_t20i = pe_t20i.groupby('player_id')['season'].max().reset_index().rename(columns={'season': 'last_t20i_season'})
player_info = player_info.merge(last_t20i, on='player_id', how='left')

# Players not in 2026 squad
not_in_2026 = player_info[player_info['last_ipl_squad_season'] < 2026]
print(f'Total IPL players in dataset: {len(player_info)}')
print(f'Players in 2026 squad: {len(player_info[player_info["last_ipl_squad_season"] == 2026])}')
print(f'Players whose last IPL squad was before 2026: {len(not_in_2026)}')

print("\n--- SAMPLE OF PLAYERS NOT IN 2026 SQUAD ---")
for idx, r in not_in_2026.sort_values('player_name').head(40).iterrows():
    print(f"{r['player_id']}: {r['player_name']} | last_squad: {r['last_ipl_squad_season']} | last_played_ipl: {r['last_ipl_played_season']} | last_t20i: {r['last_t20i_season']}")
