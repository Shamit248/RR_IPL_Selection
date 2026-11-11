import pandas as pd
from check_remaining_breakdown import rem

print("All 313 remaining players:")
for i, (idx, r) in enumerate(rem.iterrows()):
    print(f"{r['player_id']}: {r['player_name']}", end=", ")
    if (i+1) % 4 == 0:
        print()
print()
