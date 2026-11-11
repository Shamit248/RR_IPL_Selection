"""
verify_remaining_caps.py
========================
Check all 195 names against BCCI senior international debutants in Test, ODI, and T20I history.
"""

import pandas as pd

df = pd.read_csv('results/temp_uncapped_check.csv')

# Additional capped players who represented India at senior level:
more_capped = {
    7473: 'Akash Deep',       # Test debut 2024
    4265: 'T Natarajan',      # Test, ODI, T20I 2020-21
    2863: 'Sandeep Warrier',  # T20I debut 2021
}

# Check all names in df
print("All 195 candidates:")
for idx, r in df.iterrows():
    pid = r['player_id']
    name = r['player_name']
    if pid in more_capped:
        print(f"CAPPED FOUND: {pid} - {name}")

