"""
check_marquee_ids.py
====================
Verify IDs of all marquee players across the 477 player dataset.
"""

import pandas as pd

fit = pd.read_csv('results/player_fit_scores.csv')

marquee_names = [
    'bumrah', 'kohli', 'rohit', 'hardik', 'gill', 'surya', 'samson', 'jaiswal',
    'parag', 'gaikwad', 'axar', 'kuldeep', 'klaasen', 'narine', 'russell',
    'pooran', 'head', 'cummins', 'rashid khan', 'pathirana'
]

print("Found Marquee Players in fit:")
for idx, r in fit.iterrows():
    name = str(r['player_name']).lower()
    for m in marquee_names:
        if m in name:
            print(f"  ID: {r['player_id']:5d} | {r['player_name']:<30} | RR26: {r['rr_squad_2026']}")
            break

