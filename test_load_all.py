import pandas as pd
import numpy as np

# Load tables
fit = pd.read_csv("results/player_fit_scores.csv")
press = pd.read_csv("results/pressure_player_metrics.csv")
rel = pd.read_csv("results/player_reliability.csv")
bat = pd.read_csv("results/player_batting_metrics.csv")
bowl = pd.read_csv("results/player_bowling_metrics.csv")
status = pd.read_csv("results/player_status.csv")
pe = pd.read_csv("6af3166e7b922_data_pack/playing_eleven.csv")
comp_map = pd.read_csv("6af3166e7b922_data_pack/competition_team_player_mapping.csv")

print("Checking player metrics shapes and coverage...")
print("fit rows:", len(fit))
print("status rows:", len(status))
