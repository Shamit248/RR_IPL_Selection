import pandas as pd
import numpy as np

# Load player_fit_scores and player_status
fit = pd.read_csv("results/player_fit_scores.csv")
status = pd.read_csv("results/player_status.csv")

# Merge status into fit
# Note: drop availability_status in fit if status has it, to avoid collision
if 'availability_status' in fit.columns:
    fit = fit.drop(columns=['availability_status'])

merged = fit.merge(status[['player_id', 'current_active_status', 'retirement_status', 'ipl_2027_status', 'status_source', 'status_date', 'eligibility_reason', 'final_eligible']], on='player_id', how='left')

# In case any player in fit wasn't in status, default
merged['final_eligible'] = merged['final_eligible'].fillna('UNKNOWN')
merged['ipl_2027_status'] = merged['ipl_2027_status'].fillna('UNKNOWN')

# Define Batting Pressure Index / Score for Batters
# Composite metric: 40% pressure_SR, 20% pressure_delta_SR, 20% pressure_avg, 20% reliability_norm
batters = merged[merged['balls_faced'] >= 30].copy()
# Normalize components
def norm(s):
    mi, ma = s.quantile(0.05), s.quantile(0.95)
    return ((s.clip(mi, ma) - mi) / (ma - mi) * 100).clip(0, 100)

def inv_norm(s):
    return 100 - norm(s)

batters['bat_pressure_composite'] = (
    0.40 * norm(batters['pressure_SR'].fillna(120)) +
    0.20 * norm(batters['pressure_delta_SR'].fillna(0)) +
    0.20 * norm(batters['pressure_avg'].clip(upper=60).fillna(20)) +
    0.20 * batters['reliability_norm'].fillna(50)
)

print("--- POPULATION A: HISTORICAL TOP 10 BATTERS (All players, no status filter) ---")
hist_bat = batters.sort_values('bat_pressure_composite', ascending=False).head(10)
print(hist_bat[['player_id', 'player_name', 'determined_role', 'pressure_SR', 'pressure_delta_SR', 'reliability_norm', 'bat_pressure_composite', 'current_active_status', 'final_eligible']].to_string())

print("\n--- POPULATION B: IPL 2027 ELIGIBLE TOP 10 BATTERS (final_eligible == TRUE) ---")
elig_bat = batters[batters['final_eligible'] == 'TRUE'].sort_values('bat_pressure_composite', ascending=False).head(10)
print(elig_bat[['player_id', 'player_name', 'determined_role', 'pressure_SR', 'pressure_delta_SR', 'reliability_norm', 'bat_pressure_composite', 'ipl_2027_status']].to_string())

# Bowlers
bowlers = merged[merged['balls_bowled'] >= 30].copy()
bowlers['bowl_pressure_composite'] = (
    0.35 * inv_norm(bowlers['pressure_economy'].fillna(9.5)) +
    0.25 * norm(bowlers['pressure_wicket_rate'].fillna(0.04)) +
    0.20 * inv_norm(bowlers['pressure_delta_economy'].fillna(0)) +
    0.20 * bowlers['reliability_norm'].fillna(50)
)

print("\n--- POPULATION A: HISTORICAL TOP 10 BOWLERS (All players, no status filter) ---")
hist_bowl = bowlers.sort_values('bowl_pressure_composite', ascending=False).head(10)
print(hist_bowl[['player_id', 'player_name', 'determined_role', 'pressure_economy', 'pressure_wicket_rate', 'reliability_norm', 'bowl_pressure_composite', 'current_active_status', 'final_eligible']].to_string())

print("\n--- POPULATION B: IPL 2027 ELIGIBLE TOP 10 BOWLERS (final_eligible == TRUE) ---")
elig_bowl = bowlers[bowlers['final_eligible'] == 'TRUE'].sort_values('bowl_pressure_composite', ascending=False).head(10)
print(elig_bowl[['player_id', 'player_name', 'determined_role', 'pressure_economy', 'pressure_wicket_rate', 'reliability_norm', 'bowl_pressure_composite', 'ipl_2027_status']].to_string())
