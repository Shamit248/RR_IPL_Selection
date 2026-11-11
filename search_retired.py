import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
p_unique = comp_map[['player_id', 'player_name']].drop_duplicates()

search_names = [
    'Dinesh Karthik', 'Dhawan', 'Rayudu', 'Pollard', 'Bravo', 'Uthappa', 'Raina', 
    'Finch', 'Saha', 'Wade', 'Jadhav', 'Aaron', 'Nadeem', 'Mishra', 'Bracken', 
    'Gurkeerat', 'Siddarth Kaul', 'Chawla', 'Morgan', 'Gayle', 'de Villiers', 
    'Broad', 'Anderson', 'Guptill', 'Malinga', 'Watson', 'Tahir', 
    'Manoj Tiwary', 'Unmukt Chand'
]

for name in search_names:
    matches = p_unique[p_unique['player_name'].str.contains(name, case=False, na=False)]
    for idx, r in matches.iterrows():
        print(f"{r['player_id']}: {r['player_name']}")
