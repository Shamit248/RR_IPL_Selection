import pandas as pd
import numpy as np

fit = pd.read_csv('results/player_fit_scores.csv')
press = pd.read_csv('results/pressure_player_metrics.csv').set_index('player_id')
rel = pd.read_csv('results/player_reliability.csv').set_index('player_id')

pids = [23467, 36982, 35318, 7327, 8101, 2756]
for pid in pids:
    r = fit[fit['player_id'] == pid].iloc[0]
    p_info = press.loc[pid] if pid in press.index else {}
    r_info = rel.loc[pid] if pid in rel.index else {}
    
    # check confidence
    conf = r.get('confidence_score')
    if pd.isna(conf):
        conf = p_info.get('confidence_score_bowl', 50.0) if hasattr(p_info, 'get') else 50.0
    if pd.isna(conf):
        conf = 50.0
        
    # check reliability
    reli = r.get('reliability_score')
    if pd.isna(reli):
        reli = r_info.get('reliability_score_bowl', 50.0) if hasattr(r_info, 'get') else 50.0
    if pd.isna(reli):
        reli = 50.0
        
    # check pressure delta
    delta = r.get('pressure_delta')
    if pd.isna(delta):
        eco_delta = p_info.get('pressure_delta_economy', 0.0) if hasattr(p_info, 'get') else 0.0
        if not pd.isna(eco_delta):
            delta = -1.0 * float(eco_delta)
        else:
            delta = 0.0
            
    print(f"{r['player_name']} (ID {pid}): conf={conf:.1f}, reli={reli:.1f}, delta={delta:.2f}")

