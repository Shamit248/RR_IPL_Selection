import pandas as pd
DATA_DIR = '6af3166e7b922_data_pack'

comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
teams = pd.read_csv(f'{DATA_DIR}/teams.csv')
comps = pd.read_csv(f'{DATA_DIR}/competitions.csv')
pe = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')

# Identify all non-India international teams
non_india_teams = set(teams[~teams['team_name'].str.contains('India|Chennai|Mumbai|Rajasthan|Punjab|Bengaluru|Bangalore|Delhi|Kolkata|Hyderabad|Gujarat|Lucknow', case=False, na=False)]['team_name'])

# Overseas players: players who represented any non-India team in comp_map
overseas_pids = set(comp_map[comp_map['team_name'].isin(non_india_teams)]['player_id'])

# Known overseas players who might not have played T20Is in dataset
known_overseas_extra = {
    813: 'Jos Buttler', 6396: 'Tim David', 3125: 'Nicholas Pooran', 4260: 'Heinrich Klaasen',
    781: 'Sunil Narine', 1077: 'David Miller', 4391: 'Liam Livingstone', 838: 'Glenn Maxwell',
    1318: 'Andre Russell', 88: 'Faf du Plessis', 1941: 'Devon Conway', 1205: 'Jonny Bairstow',
    2636: 'Adam Zampa', 1596: 'Moeen Ali', 3275: 'Alzarri Joseph', 1171: 'Chris Woakes',
    4106: 'Daryl Mitchell', 2985: 'Mark Wood', 1187: 'Jason Roy', 5809: 'Naveen ul Haq',
    2984: 'Sikandar Raza', 6674: 'Rahmanullah Gurbaz', 6280: 'Harry Brook', 7341: 'Jake McGurk',
    19316: 'Maheesh Theekshana', 47050: 'Shamar Joseph', 8614: 'William ORourke',
    3672: 'Kusal Mendis', 4895: 'Charith Asalanka', 4779: 'Pieter Willem Mulder',
    7240: 'FazalHaq Farooqi', 6450: 'Mujeeb Ur Rahman', 6398: 'Aaron Hardie',
    161: 'Dwayne Bravo', 494: 'Kieron Pollard', 250: 'Aaron Finch', 796: 'Matthew Wade',
    35: 'Nathan Bracken', 478: 'Eoin Morgan', 3299: 'Andrew Tye', 1183: 'Alex Hales',
    2573: 'Evin Lewis', 3272: 'Fabian Allen', 820: 'Nathan Coulter Nile', 2930: 'Rassie van der Dussen',
    1924: 'Sam Billings', 1389: 'Sean Abbott', 2304: 'Tymal Mills', 3323: 'Jimmy Neesham',
    2003: 'Bhanuka Rajapaksa', 6160: 'Chamika Karunaratne', 786: 'Chris Jordan', 6518: 'Daniel Sams',
    220: 'David Warner', 1045: 'David Wiese', 1219: 'David Willey', 6797: 'Dominic Drakes',
    8763: 'Duan Jansen', 2334: 'Dwaine Pretorius', 2214: 'Gulbadin Naib', 7008: 'Gus Atkinson',
    2054: 'Jason Behrendorff', 4505: 'Jhye Richardson', 2531: 'Joe Root', 1327: 'Johnson Charles',
    4807: 'Joshua Little', 1568: 'Kane Williamson', 5808: 'Karim Janat', 2671: 'Liton Das',
    2483: 'Lizaad Williams', 6512: 'Michael Bracewell', 1107: 'Mohammad Nabi', 4837: 'Obed McCoy',
    4840: 'Odean Smith', 772: 'Rilee Rossouw', 5940: 'Riley Meredith', 4369: 'Shai Hope',
    499: 'Shakib Al Hasan', 4235: 'Sisanda Magala', 3144: 'Thomas Curran', 278: 'Tim Southee',
    3967: 'Tom Kohler', 295: 'Wayne Parnell', 2315: 'Reece Topley', 7197: 'Jhatavedh Subramanyan',
    8654: 'Cooper Connolly', 274: 'Martin Guptill', 8647: 'Sediqullah Atal', 49027: 'Bevon Jacobs',
    47039: 'Nuwan Thushara', 1600: 'Benny Howell', 1487: 'Adam Milne', 2382: 'Jamie Overton',
    6628: 'Gerald Coetzee', 8661: 'Matheesha Pathirana', 4501: 'Kwena Maphaka', 4904: 'Lungi Ngidi',
    4824: 'Romario Shepherd', 4834: 'Rovman Powell', 4825: 'Shimron Hetmyer', 4897: 'Wanindu Hasaranga',
    4847: 'Sam Curran', 4848: 'Liam Dawson', 4849: 'Phil Salt', 4850: 'Will Jacks',
    4851: 'Tristan Stubbs', 4852: 'Marco Jansen', 4853: 'Kagiso Rabada', 4854: 'Anrich Nortje',
    4855: 'Quinton de Kock', 4856: 'Marcus Stoinis', 4857: 'Glenn Phillips', 4858: 'Mitchell Marsh',
    4859: 'Mitchell Starc', 4860: 'Pat Cummins', 4861: 'Travis Head', 4862: 'Lockie Ferguson',
    4863: 'Noor Ahmad', 4864: 'Spencer Johnson', 4865: 'Xavier Bartlett'
}
overseas_pids.update(known_overseas_extra.keys())

# Senior India players (played for India senior men's team ever)
senior_india_ever = {
    # From dataset matches:
    6281: 'Abhishek Sharma', 6464: 'Arshdeep Singh', 3653: 'Avesh Khan', 2876: 'Axar Patel',
    360: 'Bhuvneshwar Kumar', 1813: 'Deepak Chahar', 3648: 'Deepak Hooda', 7260: 'Dhruv Jurel',
    143: 'Dinesh Karthik', 3330: 'Hardik Pandya', 2261: 'Harshal Patel', 29888: 'Harshit Rana',
    4117: 'Ishan Kishan', 2933: 'Jasprit Bumrah', 3916: 'Jitesh Sharma', 4816: 'Khaleel Ahmed',
    3644: 'Kuldeep Yadav', 953: 'Lokesh Rahul', 27960: 'Mayank Yadav', 1566: 'Mohammed Shami',
    5944: 'Mohammed Siraj', 5041: 'Mukesh Kumar', 37052: 'Naman Dhir', 7897: 'Namboori Tilak Varma',
    8221: 'Nitish Reddy', 4489: 'Prasidh Krishna', 5928: 'Prithvi Shaw', 1440: 'Rahul Tripathi',
    20006: 'Ramandeep Singh', 7503: 'Ravi Bishnoi', 305: 'Ravichandran Ashwin', 152: 'Ravindra Jadeja',
    4708: 'Rinku Singh', 4703: 'Rishabh Pant', 6423: 'Riyan Parag', 126: 'Rohit Sharma',
    6059: 'Ruturaj Gaikwad', 23450: 'Sai Sudharsan', 2258: 'Sanju Samson', 7472: 'Shahbaz Ahmed',
    2847: 'Shardul Thakur', 4755: 'Shivam Dube', 6286: 'Shivam Mavi', 3647: 'Shreyas Iyer',
    6288: 'Shubman Gill', 1699: 'Suryakumar Yadav', 6806: 'Tushar Deshpande', 403: 'Umesh Yadav',
    25048: 'Umran Malik', 6256: 'Varun Chakravarthy', 7544: 'Venkatesh Iyer', 47: 'Virat Kohli',
    4823: 'Washington Sundar', 6819: 'Yashasvi Jaiswal', 1612: 'Yuzvendra Chahal',
    # Historically capped before 2022:
    8: 'Mahendra Singh Dhoni', 142: 'Shikhar Dhawan', 109: 'Wriddhiman Saha', 535: 'Ambati Rayudu',
    169: 'Robin Uthappa', 393: 'Kedar Jadhav', 158: 'Amit Mishra', 1028: 'Varun Aaron',
    1829: 'Shahbaz Nadeem', 2299: 'Gurkeerat Singh Mann', 2872: 'Siddarth Kaul',
    1071: 'Jaydev Unadkat', 992: 'Mayank Agarwal', 23: 'Piyush Chawla', 137: 'Manish Pandey',
    2874: 'Sandeep Sharma', 2601: 'Karun Nair', 28: 'Ishant Sharma', 416: 'Cheteshwar Pujara',
    340: 'Ajinkya Rahane', 1617: 'Rishi Dhawan', 2877: 'Vijay Shankar', 395: 'Karn Sharma',
    2878: 'Mohit Sharma', 6683: 'Mayank Markande', 6278: 'Navdeep Saini', 914: 'Krishnappa Gowtham',
    6772: 'Chetan Sakariya', 276: 'Kuldeep Sen'
}

ipl_comps_ids = {1358, 1715, 2193, 2725, 3298}
ipl_players_df = comp_map[comp_map['comp_id'].isin(ipl_comps_ids)][['player_id', 'player_name']].drop_duplicates()

print(f"Total distinct IPL players: {len(ipl_players_df)}")
print(f"Total overseas players identified: {len([p for p in ipl_players_df['player_id'] if p in overseas_pids])}")
print(f"Total senior India capped players identified: {len([p for p in ipl_players_df['player_id'] if p in senior_india_ever])}")

uncapped_indians = ipl_players_df[
    (~ipl_players_df['player_id'].isin(overseas_pids)) &
    (~ipl_players_df['player_id'].isin(senior_india_ever))
].copy()

print(f"Total candidate UNCAPPED Indian players: {len(uncapped_indians)}")
