import pandas as pd
import numpy as np

# Load player metrics
bat = pd.read_csv('results/player_batting_metrics.csv')
bowl = pd.read_csv('results/player_bowling_metrics.csv')
press = pd.read_csv('results/pressure_player_metrics.csv')
rel = pd.read_csv('results/player_reliability.csv')
roles = pd.read_csv('results/player_role_analysis.csv')

print(f"Batting metrics rows: {len(bat)}")
print(f"Bowling metrics rows: {len(bowl)}")
print(f"Pressure metrics rows: {len(press)}")
print(f"Reliability rows: {len(rel)}")
print(f"Role rows: {len(roles)}")

# Merge bat with pressure and reliability
# Check columns in bat
print("Bat columns:", [c for c in bat.columns if 'runs' in c or 'SR' in c or 'balls' in c][:10])
print("Press columns:", [c for c in press.columns if 'pressure' in c][:10])
print("Rel columns:", rel.columns.tolist()[:10])
