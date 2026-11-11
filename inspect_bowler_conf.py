import pandas as pd
press = pd.read_csv('results/pressure_player_metrics.csv')
pids = [23467, 36982]
print(press[press['player_id'].isin(pids)][['player_id', 'player_name', 'confidence_score', 'confidence_score_bowl']])

