import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
india_players = comp_map[comp_map['team_id'] == 18][['player_id', 'player_name']].drop_duplicates().sort_values('player_name')
print(f"Total India international players in dataset: {len(india_players)}")
print("All 66 players:")
for i, (idx, r) in enumerate(india_players.iterrows()):
    print(f"{r['player_id']}: {r['player_name']}", end=', ')
    if (i+1) % 4 == 0:
        print()
print()
