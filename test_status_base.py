import pandas as pd
import numpy as np

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

# Get all 477 IPL players
ipl_players = ipl_cm.groupby(['player_id', 'player_name']).agg(
    last_ipl_squad_season=('season', 'max'),
    ipl_seasons=('season', lambda s: sorted(list(set(s))))
).reset_index()

# Check IPL 2026 squad team
squad_2026 = comp_map[comp_map['comp_id'] == 3298][['player_id', 'team_name']].drop_duplicates()
ipl_players = ipl_players.merge(squad_2026.rename(columns={'team_name': 'ipl_2026_team'}), on='player_id', how='left')

# Check played in IPL 2026
pe_2026 = pe_m[(pe_m['comp_id'] == 3298) & (pe_m['is_played'] == True)]
played_2026_ids = set(pe_2026['player_id'])
ipl_players['played_ipl_2026'] = ipl_players['player_id'].isin(played_2026_ids)

# Check last IPL played season
pe_ipl = pe_m[(pe_m['comp_id'].isin(ipl_comps.keys())) & (pe_m['is_played'] == True)].copy()
last_ipl_p = pe_ipl.groupby('player_id')['season'].max().reset_index().rename(columns={'season': 'last_ipl_season'})
ipl_players = ipl_players.merge(last_ipl_p, on='player_id', how='left')
ipl_players['last_ipl_season'] = ipl_players['last_ipl_season'].fillna(ipl_players['last_ipl_squad_season']).astype(int)

# Check T20I appearances
pe_t20i = pe_m[(pe_m['match_format'] == 'T20I') & (pe_m['is_played'] == True)].copy()
last_t20i = pe_t20i.groupby('player_id')['season'].max().reset_index().rename(columns={'season': 'last_t20i_season'})
ipl_players = ipl_players.merge(last_t20i, on='player_id', how='left')

# Historical data available
bbb = pd.read_csv(f'{DATA_DIR}/ball_by_ball.csv', usecols=['striker_id', 'bowler_id'])
bbb_ids = set(bbb['striker_id']).union(set(bbb['bowler_id']))
ipl_players['historical_data_available'] = ipl_players['player_id'].isin(bbb_ids)

print(f"Total IPL players: {len(ipl_players)}")
print(f"In 2026 squad: {ipl_players['ipl_2026_team'].notna().sum()}")
print(f"Played in 2026: {ipl_players['played_ipl_2026'].sum()}")
print(f"Has historical bbb data: {ipl_players['historical_data_available'].sum()}")
print(f"Has T20I data: {ipl_players['last_t20i_season'].notna().sum()}")
