import pandas as pd

bat = pd.read_csv('results/ipl2027_eligible_top10_batters.csv')
bowl = pd.read_csv('results/ipl2027_eligible_top10_bowlers.csv')
cmap = pd.read_csv('6af3166e7b922_data_pack/competition_team_player_mapping.csv')

# Get latest team for each player
latest_team = cmap.sort_values('comp_id', ascending=False).drop_duplicates('player_id')[['player_id', 'team_name']]

bat = bat.merge(latest_team, on='player_id', how='left')
bowl = bowl.merge(latest_team, on='player_id', how='left')

print("=== TOP 10 BATTERS UNDER PRESSURE ===")
for idx, r in bat.iterrows():
    print(f"Rank {r['rank']}: {r['player_name']} (ID: {r['player_id']}) | Team: {r['team_name']} | Role: {r['determined_role']}")
    print(f"   Pressure SR: {r['pressure_SR']:.2f} (Delta: +{r['pressure_delta_SR']:.2f}) | Avg: {r['pressure_avg']:.2f} | Bnd%: {r['pressure_boundary_rate']:.2f}% | Balls: {r['pressure_balls']} | Rel: {r['reliability_score_bat']:.2f} | Score: {r['bat_pressure_score']:.2f}")

print("\n=== TOP 10 BOWLERS UNDER PRESSURE ===")
for idx, r in bowl.iterrows():
    print(f"Rank {r['rank']}: {r['player_name']} (ID: {r['player_id']}) | Team: {r['team_name']} | Role: {r['determined_role']}")
    print(f"   Pressure Econ: {r['pressure_economy']:.2f} (Delta: {r['pressure_delta_economy']:.2f}) | Wkts/Over: {r['pressure_wicket_rate']:.3f} | Dot%: {r['pressure_dot_rate']:.2f}% | Balls: {r['balls_bowled']} | Score: {r['bowl_pressure_score']:.2f}")
