import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

teams = pd.read_csv(f'{DATA_DIR}/teams.csv')
comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
comps = pd.read_csv(f'{DATA_DIR}/competitions.csv')

# Unique international teams
intl_teams = teams[teams['team_name'].isin([
    'India', 'Australia', 'England', 'South Africa', 'West Indies', 
    'New Zealand', 'Pakistan', 'Sri Lanka', 'Afghanistan', 'Bangladesh', 
    'Zimbabwe', 'Ireland', 'Netherlands', 'Scotland', 'Namibia', 'USA', 'Nepal', 'Oman', 'UAE', 'Canada'
])][['team_id', 'team_name']].drop_duplicates()

print("International teams in dataset:")
print(intl_teams.to_string())
