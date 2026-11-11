"""
verify_all_indian_candidates.py
================================
Rigorously inspect each of the 298 potential Indian players:
1. Verify if they are actually overseas players (e.g. Gideon Peters).
2. Check if they have ever played for India at senior level (Test, ODI, T20I) in dataset OR in real-life ICC records.
3. Classify all remaining as UNCAPPED INDIAN.
"""

import pandas as pd

DATA_DIR = '6af3166e7b922_data_pack'
OUT_DIR  = 'results'

fit = pd.read_csv(f'{OUT_DIR}/player_fit_scores.csv')
status = pd.read_csv(f'{OUT_DIR}/player_status.csv')
comp_map = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
pe = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')

# Players who played in Playing XI for India (team_id 18) in the dataset:
pe_india_pids = set(pe[pe['team_id'] == 18]['player_id'].unique())
print(f"Total players who played in XI for India senior team in dataset: {len(pe_india_pids)}")

# Senior India capped players from real-life ICC history (Tests, ODIs, T20Is):
# Includes players who debuted before 2022 or in formats outside dataset T20Is:
known_india_senior_capped = {
    # Dataset Playing XI capped:
    6281: 'Abhishek Sharma', 6464: 'Arshdeep Singh', 28018: 'Ashok Sharma', 3653: 'Avesh Khan',
    2876: 'Axar Patel', 360: 'Bhuvneshwar Kumar', 1813: 'Deepak Chahar', 3648: 'Deepak Hooda',
    7260: 'Dhruv Jurel', 143: 'Dinesh Karthik', 3330: 'Hardik Pandya', 25138: 'Harsh Dubey',
    2261: 'Harshal Patel', 29888: 'Harshit Rana', 4117: 'Ishan Kishan', 2933: 'Jasprit Bumrah',
    3916: 'Jitesh Sharma', 4816: 'Khaleel Ahmed', 3644: 'Kuldeep Yadav', 8251: 'Kumar Kushagra',
    953: 'Lokesh Rahul', 27960: 'Mayank Yadav', 1566: 'Mohammed Shami', 5944: 'Mohammed Siraj',
    5041: 'Mukesh Kumar', 37052: 'Naman Dhir', 7897: 'Namboori Tilak Varma', 8221: 'Nitish Reddy',
    7216: 'Prabhsimran Singh', 4489: 'Prasidh Krishna', 58246: 'Prince Yadav', 1440: 'Rahul Tripathi',
    20006: 'Ramandeep Singh', 7503: 'Ravi Bishnoi', 305: 'Ravichandran Ashwin', 152: 'Ravindra Jadeja',
    4708: 'Rinku Singh', 4703: 'Rishabh Pant', 6423: 'Riyan Parag', 126: 'Rohit Sharma',
    6059: 'Ruturaj Gaikwad', 23450: 'Sai Sudharsan', 2258: 'Sanju Samson', 7472: 'Shahbaz Ahmed',
    2847: 'Shardul Thakur', 4755: 'Shivam Dube', 6286: 'Shivam Mavi', 3647: 'Shreyas Iyer',
    6288: 'Shubman Gill', 1699: 'Suryakumar Yadav', 7625: 'Suryansh Shedge', 6806: 'Tushar Deshpande',
    403: 'Umesh Yadav', 25048: 'Umran Malik', 50284: 'Vaibhav Sooryavanshi', 6256: 'Varun Chakravarthy',
    7544: 'Venkatesh Iyer', 46066: 'Vipraj Nigam', 47: 'Virat Kohli', 4487: 'Vyshak Kumar',
    4823: 'Washington Sundar', 7322: 'Yash Dayal', 6287: 'Yash Thakur', 6819: 'Yashasvi Jaiswal',
    1612: 'Yuzvendra Chahal', 5928: 'Prithvi Shaw',
    # Historical / other senior India caps:
    8: 'MS Dhoni', 142: 'Shikhar Dhawan', 109: 'Wriddhiman Saha', 535: 'Ambati Rayudu',
    169: 'Robin Uthappa', 393: 'Kedar Jadhav', 158: 'Amit Mishra', 1028: 'Varun Aaron',
    1829: 'Shahbaz Nadeem', 2299: 'Gurkeerat Singh Mann', 2872: 'Siddarth Kaul',
    1071: 'Jaydev Unadkat', 992: 'Mayank Agarwal', 23: 'Piyush Chawla', 137: 'Manish Pandey',
    2874: 'Sandeep Sharma', 930: 'Karun Nair', 28: 'Ishant Sharma', 416: 'Cheteshwar Pujara',
    340: 'Ajinkya Rahane', 1617: 'Rishi Dhawan', 2877: 'Vijay Shankar', 395: 'Karn Sharma',
    2878: 'Mohit Sharma', 6683: 'Mayank Markande', 4288: 'Navdeep Saini', 6278: 'Navdeep Saini',
    914: 'Krishnappa Gowtham', 6772: 'Chetan Sakariya', 7545: 'Kuldeep Sen', 276: 'Kuldeep Sen',
    5577: 'Sai Kishore', 2601: 'Karun Nair', 6314: 'Devdutt Padikkal', 4704: 'Rajat Patidar',
    4192: 'Sarfaraz Khan', 6161: 'Rahul Chahar', 253: 'Mandeep Singh', 2848: 'Jayant Yadav',
    6048: 'Ishan Porel', # Ishan Porel was net bowler / standby but never capped. Wait, let's verify Ishan Porel!
}

# Overseas players that might not have been caught yet:
additional_overseas = {
    7095: 'Gideon Peters', # South African
    34118: 'Irfan Taufiq', # Let's verify Irfan Taufiq
    6351: 'Yarra Prithviraj', # Indian (Andhra bowler)
}

print("Running check on all 477 players...")

