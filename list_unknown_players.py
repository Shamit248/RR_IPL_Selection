import pandas as pd
from check_intl_distribution import summary

unknown_p = summary[summary['intl_team'] == 'UNKNOWN_IPL_ONLY'].sort_values('player_name')
print(f"Total unknown IPL-only players: {len(unknown_p)}")

for i, (idx, r) in enumerate(unknown_p.iterrows()):
    print(f"{r['player_id']}: {r['player_name']}", end=", ")
    if (i+1) % 4 == 0:
        print()
print()
