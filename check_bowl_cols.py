import pandas as pd
press = pd.read_csv("results/pressure_player_metrics.csv")
print("All bowling columns in pressure_player_metrics:")
print([c for c in press.columns if any(k in c.lower() for k in ['bowl', 'eco', 'wicket', 'dot'])])

bowl = pd.read_csv("results/player_bowling_metrics.csv")
print("\nTop 10 columns in player_bowling_metrics:")
print(bowl.columns.tolist()[:15])
