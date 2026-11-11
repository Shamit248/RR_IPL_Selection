import pandas as pd
from audit_capped_by_name import senior_india_capped_names
from classify_all_ipl_players import all_overseas_pids

top10 = pd.read_csv('results/uncapped_ipl2027_top10.csv')
pool = pd.read_csv('results/uncapped_ipl2027_candidate_pool.csv')
watch = pd.read_csv('results/uncapped_ipl2027_watchlist.csv')

print("1. Checking Top 10 for Overseas, Capped, Retired, or RR 2026 squad members:")
for idx, r in top10.iterrows():
    p_id = r['player_id']
    name = r['player_name']
    name_clean = name.strip().lower()
    
    assert p_id not in all_overseas_pids, f"ERROR: {name} is overseas!"
    assert name_clean not in senior_india_capped_names, f"ERROR: {name} is capped!"
    
    pool_row = pool[pool['player_id'] == p_id].iloc[0]
    assert pool_row['rr_squad_2026'] == False, f"ERROR: {name} is already in RR 2026 squad!"
    assert pool_row['current_active_status'] == 'ACTIVE', f"ERROR: {name} is not active!"
    assert pool_row['retirement_status'] != 'RETIRED', f"ERROR: {name} is retired!"
    
print("Top 10 checks passed with 100% compliance!")

print("\n2. Checking candidate pool totals:")
print(f"Total uncapped candidates: {len(pool)}")
print(f"Active uncapped candidates: {len(pool[pool['current_active_status'] == 'ACTIVE'])}")
print(f"Non-RR active uncapped candidates: {len(pool[(pool['current_active_status'] == 'ACTIVE') & (~pool['rr_squad_2026'])])}")
print(f"Watchlist candidates: {len(watch)}")

