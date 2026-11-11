import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
teams = pd.read_csv(f'{DATA_DIR}/teams.csv')
ipl_comps = {1358: 2022, 1715: 2023, 2193: 2024, 2725: 2025, 3298: 2026}

ipl_pids = set(comp_map[comp_map['comp_id'].isin(ipl_comps.keys())]['player_id'])
all_ipl_p = comp_map[comp_map['player_id'].isin(ipl_pids)][['player_id', 'player_name', 'team_name']].drop_duplicates()

# Group by player_id
summary = all_ipl_p.groupby(['player_id', 'player_name'])['team_name'].apply(lambda x: sorted(list(set(x)))).reset_index()

# Check for national teams in team_name
intl_teams_list = [
    'India', 'Australia', 'England', 'South Africa', 'West Indies', 
    'New Zealand', 'Pakistan', 'Sri Lanka', 'Afghanistan', 'Bangladesh', 
    'Zimbabwe', 'Ireland', 'Netherlands', 'Scotland', 'Canada', 'Oman', 'Nepal'
]

def detect_country(teams_list):
    for t in teams_list:
        if t in intl_teams_list:
            return t
    return 'UNKNOWN_IPL_ONLY'

summary['intl_team'] = summary['team_name'].apply(detect_country)
print("Distribution by intl_team:")
print(summary['intl_team'].value_counts())
