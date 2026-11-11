import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
pe = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')

india_cm = comp_map[comp_map['team_id'] == 18][['player_id', 'player_name']].drop_duplicates()
india_pe = pe[(pe['team_id'] == 18) & (pe['is_played'] == True)][['player_id']].drop_duplicates()
india_pe['actually_played_for_india_in_dataset'] = True

india_check = india_cm.merge(india_pe, on='player_id', how='left')
india_check['actually_played_for_india_in_dataset'] = india_check['actually_played_for_india_in_dataset'].fillna(False)

print("Players in India squad who DID NOT play (is_played=True) in our dataset:")
did_not_play = india_check[~india_check['actually_played_for_india_in_dataset']]
print(did_not_play.to_string())
