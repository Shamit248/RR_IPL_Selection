import pandas as pd
fit = pd.read_csv('results/player_fit_scores.csv')
rr_players = fit[fit['rr_squad_2026'] == True]
print(f"Total RR 2026 squad members in fit: {len(rr_players)}")
print(rr_players[['player_id', 'player_name', 'determined_role']].to_string())

