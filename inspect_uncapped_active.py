import pandas as pd
from audit_uncapped_pool import uncapped_indians, DATA_DIR

fit = pd.read_csv("results/player_fit_scores.csv")
status = pd.read_csv("results/player_status.csv")

uncapped = uncapped_indians.merge(fit[['player_id', 'determined_role', 'balls_faced', 'balls_bowled', 'pressure_score', 'RR_FIT_SCORE']], on='player_id', how='left')
uncapped = uncapped.merge(status[['player_id', 'current_active_status', 'ipl_2027_status', 'final_eligible']], on='player_id', how='left')

active_uncapped = uncapped[uncapped['final_eligible'] == 'TRUE'].sort_values('RR_FIT_SCORE', ascending=False)

print(f"Total Active Eligible Uncapped Indian Players: {len(active_uncapped)}")
print("\nTop 30 by RR Fit Score:")
print(active_uncapped[['player_id', 'player_name', 'determined_role', 'balls_faced', 'balls_bowled', 'pressure_score', 'RR_FIT_SCORE', 'ipl_2027_status']].head(30).to_string())
