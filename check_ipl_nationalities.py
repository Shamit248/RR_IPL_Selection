import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
teams = pd.read_csv(f'{DATA_DIR}/teams.csv')
comps = pd.read_csv(f'{DATA_DIR}/competitions.csv')

ipl_comps = {1358: 2022, 1715: 2023, 2193: 2024, 2725: 2025, 3298: 2026}
ipl_players = comp_map[comp_map['comp_id'].isin(ipl_comps.keys())][['player_id', 'player_name']].drop_duplicates()

# Find non-IPL competitions each player played in
non_ipl_cm = comp_map[~comp_map['comp_id'].isin(ipl_comps.keys())].copy()
player_teams = non_ipl_cm[['player_id', 'team_name']].drop_duplicates()

# Map team_name to nationality
non_india_teams = set(teams[teams['team_name'] != 'India']['team_name']) - {
    'Chennai Super Kings', 'Mumbai Indians', 'Rajasthan Royals', 'Punjab Kings',
    'Royal Challengers Bengaluru', 'Delhi Capitals', 'Kolkata Knight Riders',
    'Sunrisers Hyderabad', 'Gujarat Titans', 'Lucknow Super Giants'
}

overseas_pids = set(player_teams[player_teams['team_name'].isin(non_india_teams)]['player_id'])
india_intl_pids = set(comp_map[comp_map['team_id'] == 18]['player_id'])

print(f"Total IPL players: {len(ipl_players)}")
print(f"IPL players with overseas national team in dataset: {len(ipl_players[ipl_players['player_id'].isin(overseas_pids)])}")
print(f"IPL players with India national team in dataset: {len(ipl_players[ipl_players['player_id'].isin(india_intl_pids)])}")

remaining = ipl_players[~ipl_players['player_id'].isin(overseas_pids) & ~ipl_players['player_id'].isin(india_intl_pids)]
print(f"Remaining IPL players (neither overseas intl nor India intl in dataset): {len(remaining)}")
print("\nSample of remaining IPL players:")
print(remaining.head(25).to_string())
