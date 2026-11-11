import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
pe = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')
teams = pd.read_csv(f'{DATA_DIR}/teams.csv')
comps = pd.read_csv(f'{DATA_DIR}/competitions.csv')

# 1. Who played for senior India (team_id 18) with is_played == True?
senior_india_played_pids = set(pe[(pe['team_id'] == 18) & (pe['is_played'] == True)]['player_id'])
print(f"Total players who played for Senior India in dataset: {len(senior_india_played_pids)}")

# 2. What about players who were capped for India historically before 2022?
# E.g., MS Dhoni, Dinesh Karthik, Shikhar Dhawan, Bhuvneshwar Kumar, Umesh Yadav, 
# Jaydev Unadkat, Mayank Agarwal, Piyush Chawla, Manish Pandey, Sandeep Sharma, 
# Karun Nair, Siddarth Kaul, Varun Aaron, Shahbaz Nadeem, Kedar Jadhav, Ambati Rayudu,
# Robin Uthappa, Suresh Raina, etc.
