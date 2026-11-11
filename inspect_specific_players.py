import pandas as pd

DATA_DIR = '6af3166e7b922_data_pack'
comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
pe = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')

check_ids = [34118, 6048, 6351, 8140, 28020, 25667, 33095, 6654, 43967, 49665, 27962, 3651, 8266, 45989, 4486, 31529, 34969, 6237, 42845, 35072, 48504, 48555, 49670, 4077, 6359, 8634, 45381, 48557, 19098, 26911, 37731, 58727, 32244, 44491, 56830, 56800, 2862, 33067, 6526, 20077, 58134, 6461, 7279, 31205, 48953, 71311, 41503, 43965, 47523, 60700, 67036, 58864, 36328, 43996, 66540, 68280, 8141, 7534, 58135, 71016, 23408, 25132, 25679, 56817, 62526, 63497, 66513, 31518, 45749, 45965]

print("Checking matches played for these IDs:")
df_pe = pe[pe['player_id'].isin(check_ids)]
print(f"Total appearances in playing_eleven: {len(df_pe)}")
print("Unique player IDs in playing_eleven:")
print(df_pe['player_id'].unique())

