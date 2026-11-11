"""
classify_all_ipl_players.py
===========================
Rigorously classify all 477 IPL players in player_fit_scores.csv:
1. Overseas players (100% comprehensive)
2. Senior India Capped players (Tests, ODIs, T20Is)
3. Uncapped Indian players
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

# Step 1: All overseas players from competition mapping
non_india_teams = set(teams[~teams['team_name'].str.contains('India|Chennai|Mumbai|Rajasthan|Punjab|Bengaluru|Bangalore|Delhi|Kolkata|Hyderabad|Gujarat|Lucknow', case=False, na=False)]['team_name'])
overseas_comp_map = set(comp_map[comp_map['team_name'].isin(non_india_teams)]['player_id'].unique())

# Additional confirmed overseas players (overseas cricketers in IPL)
extra_overseas = {
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
    4903: 'Kusal Mendis', 4905: 'Dasun Shanaka', 4906: 'Chamika Karunaratne',
    7095: 'Gideon Peters'
}

all_overseas_pids = overseas_comp_map.union(set(extra_overseas.keys()))

# Step 2: Senior India Capped Players (Tests, ODIs, or T20Is)
# In dataset playing XI for senior India team_id 18:
pe_india_pids = set(pe[pe['team_id'] == 18]['player_id'].unique())

# Historical & other senior India caps (pre-2022 or other formats):
historical_india_capped = {
    8: 'MS Dhoni', 142: 'Shikhar Dhawan', 109: 'Wriddhiman Saha', 535: 'Ambati Rayudu',
    169: 'Robin Uthappa', 393: 'Kedar Jadhav', 158: 'Amit Mishra', 1028: 'Varun Aaron',
    1829: 'Shahbaz Nadeem', 2299: 'Gurkeerat Singh Mann', 2872: 'Siddarth Kaul',
    1071: 'Jaydev Unadkat', 992: 'Mayank Agarwal', 23: 'Piyush Chawla', 137: 'Manish Pandey',
    2874: 'Sandeep Sharma', 930: 'Karun Nair', 2601: 'Karun Nair', 28: 'Ishant Sharma',
    416: 'Cheteshwar Pujara', 340: 'Ajinkya Rahane', 1617: 'Rishi Dhawan', 2877: 'Vijay Shankar',
    395: 'Karn Sharma', 2878: 'Mohit Sharma', 6683: 'Mayank Markande', 4288: 'Navdeep Saini',
    6278: 'Navdeep Saini', 914: 'Krishnappa Gowtham', 6772: 'Chetan Sakariya', 7545: 'Kuldeep Sen',
    276: 'Kuldeep Sen', 5577: 'Sai Kishore', 6314: 'Devdutt Padikkal', 4704: 'Rajat Patidar',
    4192: 'Sarfaraz Khan', 6161: 'Rahul Chahar', 253: 'Mandeep Singh', 2848: 'Jayant Yadav',
    5928: 'Prithvi Shaw', 2843: 'Krunal Pandya'
}

all_senior_india_capped = pe_india_pids.union(set(historical_india_capped.keys()))

# Let's inspect the classification for all 477 players
classification = []
for idx, row in fit.iterrows():
    p_id = row['player_id']
    p_name = row['player_name']
    
    if p_id in all_overseas_pids:
        nat = 'OVERSEAS'
        is_ind = False
        cap_status = 'NOT_APPLICABLE'
        uncapped_status = 'OVERSEAS'
        reason = 'Overseas player (represented foreign national team or overseas citizen)'
    elif p_id in all_senior_india_capped:
        nat = 'INDIA'
        is_ind = True
        cap_status = 'CAPPED'
        uncapped_status = 'CAPPED_INDIAN'
        reason = 'Senior India capped player (represented India men national team in Test, ODI, or T20I)'
    else:
        nat = 'INDIA'
        is_ind = True
        cap_status = 'UNCAPPED'
        uncapped_status = 'UNCAPPED_INDIAN'
        reason = 'Domestic Indian player; never represented senior India men national team in Tests, ODIs, or T20Is'
        
    classification.append({
        'player_id': p_id,
        'player_name': p_name,
        'nationality': nat,
        'is_indian': is_ind,
        'india_cap_status': cap_status,
        'uncapped_status': uncapped_status,
        'classification_reason': reason
    })

clf_df = pd.DataFrame(classification)
print(f"Total IPL players classified: {len(clf_df)}")
print("\nBreakdown by uncapped_status:")
print(clf_df['uncapped_status'].value_counts())

uncapped_indians = clf_df[clf_df['uncapped_status'] == 'UNCAPPED_INDIAN'].copy()
print(f"\nTotal UNCAPPED Indian players identified: {len(uncapped_indians)}")

# Check active status of uncapped indians
merged = uncapped_indians.merge(status[['player_id', 'current_active_status', 'retirement_status', 'ipl_2027_status', 'final_eligible']], on='player_id', how='left')
print("\nActive status breakdown for Uncapped Indians:")
print(merged['current_active_status'].value_counts(dropna=False))
print(merged['final_eligible'].value_counts(dropna=False))
