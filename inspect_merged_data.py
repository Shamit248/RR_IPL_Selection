import pandas as pd

bat = pd.read_csv("results/player_batting_metrics.csv")
bowl = pd.read_csv("results/player_bowling_metrics.csv")
press = pd.read_csv("results/pressure_player_metrics.csv")
rel = pd.read_csv("results/player_reliability.csv")
status = pd.read_csv("results/player_status.csv")

print("Bat shape:", bat.shape)
print("Bowl shape:", bowl.shape)
print("Press shape:", press.shape)
print("Rel shape:", rel.shape)
print("Status shape:", status.shape)

# Let's see columns in bat merged with press and rel
bat_full = bat.merge(press[['player_id', 'pressure_SR', 'pressure_delta_SR', 'pressure_avg', 'pressure_boundary_rate', 'pressure_balls', 'confidence_score_bat']], left_on='striker_id', right_on='player_id', how='left')
bat_full = bat_full.merge(rel[['player_id', 'reliability_score_bat', 'mtm_SR_variance']], on='player_id', how='left')
bat_full = bat_full.merge(status[['player_id', 'current_active_status', 'ipl_2027_status', 'final_eligible', 'eligibility_reason']], on='player_id', how='left')

print("\nSample merged bat_full columns:", bat_full.columns.tolist()[:15])
