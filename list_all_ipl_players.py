import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
teams = pd.read_csv(f'{DATA_DIR}/teams.csv')
ipl_comps = {1358: 2022, 1715: 2023, 2193: 2024, 2725: 2025, 3298: 2026}

ipl_players = comp_map[comp_map['comp_id'].isin(ipl_comps.keys())][['player_id', 'player_name']].drop_duplicates().sort_values('player_name')

print(f"Total IPL players: {len(ipl_players)}")
