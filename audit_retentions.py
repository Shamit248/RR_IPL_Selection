"""
audit_retentions.py
===================
Verify franchise retentions for top 50 performance players.
"""

import pandas as pd

perf = pd.read_csv('results/ipl2027_performance_ranking.csv')
print("Top 30 in Performance Ranking:")
for idx, r in perf.head(30).iterrows():
    print(f"#{r['performance_rank']:2d}: {r['player_name']} (ID: {r['player_id']}) | Cat: {r['player_category']:<15} | Role: {r['primary_role']:<20} | Score: {r['final_rr_2027_fit_score']:.2f}")

