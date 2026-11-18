import pandas as pd
bat = pd.read_csv('outputs/top15_ensemble_batters.csv')
bowl = pd.read_csv('outputs/top15_ensemble_bowlers.csv')

print('=== TOP 15 BATTERS ===')
for _, r in bat.iterrows():
    print(f"{int(r['final_rank']):2d} | ID:{int(r['striker_id']):5d} | {str(r['player_name']):20s} | Date:{r['latest_match_date']} | HP Balls:{int(r['hp_balls']):3d} | M1_rk:{int(r['rank_m1']):2d} (Z:{r['z_score_m1']:+.2f}) | M2_rk:{int(r['rank_m2']):2d} (Z:{r['z_score_m2']:+.2f}) | M3_rk:{int(r['rank_m3']):2d} (Z:{r['z_score_m3']:+.2f}) | RRF:{r['rrf_score']:.4f} | Final:{r['final_ensemble_score']:6.2f} | IPL:{r['ipl_teams']}")

print('\n=== TOP 15 BOWLERS ===')
for _, r in bowl.iterrows():
    print(f"{int(r['final_rank']):2d} | ID:{int(r['bowler_id']):5d} | {str(r['player_name']):20s} | Date:{r['latest_match_date']} | HP Balls:{int(r['hp_balls']):3d} | M1_rk:{int(r['rank_m1']):2d} (Z:{r['z_score_m1']:+.2f}) | M2_rk:{int(r['rank_m2']):2d} (Z:{r['z_score_m2']:+.2f}) | M3_rk:{int(r['rank_m3']):2d} (Z:{r['z_score_m3']:+.2f}) | RRF:{r['rrf_score']:.4f} | Final:{r['final_ensemble_score']:6.2f} | IPL:{r['ipl_teams']}")

