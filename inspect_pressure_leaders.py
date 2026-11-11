import pandas as pd
press = pd.read_csv("results/pressure_player_metrics.csv")
rel = pd.read_csv("results/player_reliability.csv")
bat = pd.read_csv("results/player_batting_metrics.csv")
bowl = pd.read_csv("results/player_bowling_metrics.csv")
roles = pd.read_csv("results/player_role_analysis.csv")

print("--- TOP 15 BATTERS BY PRESSURE SR (min 30 pressure balls) ---")
press_bat = press[press['pressure_balls'] >= 30].sort_values('pressure_SR', ascending=False)
print(press_bat[['player_id', 'player_name', 'pressure_balls', 'pressure_SR', 'pressure_delta_SR', 'pressure_avg']].head(15).to_string())

print("\n--- TOP 15 BOWLERS BY PRESSURE ECONOMY (min 30 pressure balls) ---")
press_bowl = press[press['bowling_pressure_balls'] >= 30].sort_values('pressure_economy', ascending=True)
print(press_bowl[['player_id', 'player_name', 'bowling_pressure_balls', 'pressure_economy', 'pressure_delta_economy', 'pressure_wicket_rate']].head(15).to_string())
