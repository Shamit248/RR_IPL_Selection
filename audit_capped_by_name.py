"""
audit_capped_by_name.py
========================
Cross-reference player names across all 477 players to catch any player_id variants of:
1. Senior India Capped players
2. Overseas players
"""

import pandas as pd

fit = pd.read_csv('results/player_fit_scores.csv')

# Complete list of senior India capped players by name (lower case clean)
senior_india_capped_names = {
    'abhishek sharma', 'arshdeep singh', 'ashok sharma', 'avesh khan', 'axar patel',
    'bhuvneshwar kumar', 'deepak chahar', 'deepak hooda', 'dhruv jurel', 'dinesh karthik',
    'hardik pandya', 'harsh dubey', 'harshal patel', 'harshit rana', 'ishan kishan',
    'jasprit bumrah', 'jitesh sharma', 'khaleel ahmed', 'kuldeep yadav', 'kumar kushagra',
    'lokesh rahul', 'kl rahul', 'mayank yadav', 'mohammed shami', 'mohammed siraj',
    'mukesh kumar', 'naman dhir', 'namboori tilak varma', 'tilak varma', 'nitish reddy',
    'nitish kumar reddy', 'prabhsimran singh', 'prasidh krishna', 'prince yadav',
    'rahul tripathi', 'ramandeep singh', 'ravi bishnoi', 'ravichandran ashwin',
    'ravindra jadeja', 'rinku singh', 'rishabh pant', 'riyan parag', 'rohit sharma',
    'ruturaj gaikwad', 'sai sudharsan', 'sanju samson', 'shahbaz ahmed', 'shardul thakur',
    'shivam dube', 'shivam mavi', 'shreyas iyer', 'shubman gill', 'suryakumar yadav',
    'suryansh shedge', 'tushar deshpande', 'umesh yadav', 'umran malik', 'vaibhav sooryavanshi',
    'varun chakravarthy', 'venkatesh iyer', 'vipraj nigam', 'virat kohli', 'vyshak kumar',
    'vijaykumar vyshak', 'washington sundar', 'yash dayal', 'yash thakur', 'yashasvi jaiswal',
    'yuzvendra chahal', 'prithvi shaw', 'mahendra singh dhoni', 'ms dhoni', 'shikhar dhawan',
    'wriddhiman saha', 'ambati rayudu', 'robin uthappa', 'kedar jadhav', 'amit mishra',
    'varun aaron', 'shahbaz nadeem', 'gurkeerat singh mann', 'siddarth kaul', 'jaydev unadkat',
    'mayank agarwal', 'piyush chawla', 'manish pandey', 'sandeep sharma', 'karun nair',
    'ishant sharma', 'cheteshwar pujara', 'ajinkya rahane', 'rishi dhawan', 'vijay shankar',
    'karn sharma', 'mohit sharma', 'mayank markande', 'navdeep saini', 'krishnappa gowtham',
    'chetan sakariya', 'kuldeep sen', 'sai kishore', 'r sai kishore', 'devdutt padikkal',
    'rajat patidar', 'sarfaraz khan', 'rahul chahar', 'mandeep singh', 'jayant yadav',
    'krunal pandya', 'nitish rana', 'sanju v samson', 'shivam ravi dube', 'harpreet singh bhatia',
    'pawan negi', 'barinder sran', 'faiz fazal', 'parvez rasool', 'pankaj singh', 'vinay kumar'
}

matches_found = []
for idx, r in fit.iterrows():
    p_name = str(r['player_name']).strip().lower()
    p_id = r['player_id']
    if p_name in senior_india_capped_names:
        matches_found.append((p_id, r['player_name']))

print(f"Total capped player occurrences by name in 477 IPL list: {len(matches_found)}")
for pid, name in sorted(matches_found, key=lambda x: x[1]):
    print(f"  ID: {pid} | {name}")

