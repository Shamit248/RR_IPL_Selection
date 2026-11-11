"""
audit_full_classification.py
============================
Audit and rigorously classify all 477 IPL players into:
- OVERSEAS
- CAPPED_INDIAN
- UNCAPPED_INDIAN
"""

import pandas as pd
import numpy as np

DATA_DIR = '6af3166e7b922_data_pack'
OUT_DIR  = 'results'

fit = pd.read_csv(f'{OUT_DIR}/player_fit_scores.csv')
status = pd.read_csv(f'{OUT_DIR}/player_status.csv')
comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
teams = pd.read_csv(f'{DATA_DIR}/teams.csv')
pe = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')

# 1. Non-India international teams
non_india_teams = set(teams[~teams['team_name'].str.contains('India|Chennai|Mumbai|Rajasthan|Punjab|Bengaluru|Bangalore|Delhi|Kolkata|Hyderabad|Gujarat|Lucknow', case=False, na=False)]['team_name'])
overseas_from_comp_map = set(comp_map[comp_map['team_name'].isin(non_india_teams)]['player_id'])

# Known overseas players not in international T20s in dataset
known_overseas = {
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
    4863: 'Noor Ahmad', 4864: 'Spencer Johnson', 4865: 'Xavier Bartlett',
    19315: 'Vijayakanth Viyaskanth', 22920: 'Jacob Duffy', 6931: 'Pathum Nissanka',
    39657: 'Eshan Malinga', 4229: 'George Linde', 1556: 'David Payne',
    3151: 'Sam Billings', 2608: 'Ben McDermott', 4233: 'Dwaine Pretorius',
    6570: 'Dunith Wellalage', 6848: 'Matheesha Pathirana', 2043: 'Taskin Ahmed',
    1244: 'Mustafizur Rahman', 2937: 'Dushmantha Chameera', 2042: 'Shakib Al Hasan',
    1206: 'Sam Curran', 2291: 'Tom Curran', 841: 'Josh Hazlewood', 837: 'Steve Smith',
    839: 'Mitchell Starc', 840: 'Pat Cummins', 842: 'David Warner', 843: 'Aaron Finch',
    2407: 'Trent Boult', 2408: 'Tim Southee', 2409: 'Kane Williamson', 2410: 'Mitchell Santner',
    2411: 'Glenn Phillips', 2412: 'Devon Conway', 2413: 'Finn Allen', 2414: 'Daryl Mitchell',
    2415: 'Lockie Ferguson', 2416: 'Adam Milne', 2417: 'Ish Sodhi', 2418: 'Matt Henry',
    1639: 'Quinton de Kock', 1640: 'Kagiso Rabada', 1641: 'Anrich Nortje', 1642: 'Lungi Ngidi',
    1643: 'David Miller', 1644: 'Aiden Markram', 1645: 'Heinrich Klaasen', 1646: 'Marco Jansen',
    1647: 'Keshav Maharaj', 1648: 'Tabraiz Shamsi', 1649: 'Tristan Stubbs', 1650: 'Gerald Coetzee',
    1651: 'Nandre Burger', 1652: 'Bjorn Fortuin', 1653: 'Andile Phehlukwayo',
    1172: 'Ben Stokes', 1173: 'Jos Buttler', 1174: 'Jonny Bairstow', 1175: 'Liam Livingstone',
    1176: 'Sam Curran', 1177: 'Moeen Ali', 1178: 'Chris Woakes', 1179: 'Mark Wood',
    1180: 'Jofra Archer', 1181: 'Adil Rashid', 1182: 'Reece Topley', 1184: 'Phil Salt',
    1185: 'Harry Brook', 1186: 'Will Jacks', 1188: 'Gus Atkinson', 1189: 'Tom Hartley',
    2574: 'Nicholas Pooran', 2575: 'Shimron Hetmyer', 2576: 'Andre Russell', 2577: 'Sunil Narine',
    2578: 'Rovman Powell', 2579: 'Romario Shepherd', 2580: 'Alzarri Joseph', 2581: 'Akeal Hosein',
    2582: 'Jason Holder', 2583: 'Kyle Mayers', 2584: 'Shamar Joseph', 2585: 'Gudakesh Motie',
    2586: 'Sherfane Rutherford', 2587: 'Johnson Charles', 2588: 'Brandon King', 2589: 'Shai Hope',
    2590: 'Obed McCoy', 2591: 'Odean Smith',
    5810: 'Rashid Khan', 5811: 'Mohammad Nabi', 5812: 'Mujeeb Ur Rahman', 5813: 'Fazalhaq Farooqi',
    5814: 'Naveen-ul-Haq', 5815: 'Noor Ahmad', 5816: 'Rahmanullah Gurbaz', 5817: 'Azmatullah Omarzai',
    5818: 'Gulbadin Naib', 5819: 'Najibullah Zadran',
    4896: 'Wanindu Hasaranga', 4898: 'Maheesh Theekshana', 4899: 'Matheesha Pathirana',
    4900: 'Dilshan Madushanka', 4901: 'Nuwan Thushara', 4902: 'Charith Asalanka',
    4903: 'Kusal Mendis', 4905: 'Dasun Shanaka', 4906: 'Chamika Karunaratne'
}

all_overseas = overseas_from_comp_map.union(set(known_overseas.keys()))

# Check which players in fit are in all_overseas
fit_players = fit[['player_id', 'player_name', 'rr_squad_2026']].drop_duplicates()
print(f"Total players in player_fit_scores: {len(fit_players)}")

# Let's inspect all players in fit_players not in all_overseas
potential_indians = fit_players[~fit_players['player_id'].isin(all_overseas)]
print(f"Potential Indian players: {len(potential_indians)}")

# Check if any remaining potential_indians are overseas players we missed
for idx, r in potential_indians.iterrows():
    # Print if name looks overseas or uncommon
    p_id = r['player_id']
    p_name = r['player_name']
    # Let's check comp_map for this player
    player_teams = comp_map[comp_map['player_id'] == p_id]['team_name'].unique()
    print(f"{p_id}: {p_name} -> Teams: {list(player_teams)}")

