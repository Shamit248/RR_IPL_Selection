import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
pe = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')

# Check Sai Kishore (5577)
sk = comp_map[comp_map['player_id'] == 5577]
print("Sai Kishore in comp_map:")
print(sk[['comp_id', 'comp_name', 'team_id', 'team_name']].to_string())

# Check all Asian Games / other competitions in comps
comps = pd.read_csv(f'{DATA_DIR}/competitions.csv')
print("\nCompetitions involving India (team_id 18 or similar):")
india_comps = comp_map[comp_map['team_id'] == 18]['comp_id'].unique()
print(comps[comps['comp_id'].isin(india_comps)][['comp_id', 'comp_name', 'match_format', 'season']].to_string())
