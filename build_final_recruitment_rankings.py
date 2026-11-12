"""
build_final_recruitment_rankings.py
===================================
Comprehensive script to generate the final Rajasthan Royals IPL 2027 recruitment intelligence:
1. Performance Ranking (results/ipl2027_performance_ranking.csv)
2. Recruitment Ranking (results/rr_ipl2027_recruitment_ranking.csv)
3. Top 20 Combined (results/rr_ipl2027_top20.csv)
4. Capped Top 10 (results/rr_ipl2027_capped_top10.csv)
5. Uncapped Top 10 (results/rr_ipl2027_uncapped_top10.csv)
6. Final Combined Top 10 (results/rr_ipl2027_final_top10.csv)
7. Role-Wise Targets (results/rr_ipl2027_role_targets.csv)
8. Value vs Upside Matrix (results/rr_ipl2027_value_upside_matrix.csv)
"""

import os
import pandas as pd
import numpy as np

DATA_DIR = '6af3166e7b922_data_pack'
OUT_DIR  = 'results'

print("--- Step 1: Loading existing analysis files ---")
fit_df        = pd.read_csv(f'{OUT_DIR}/player_fit_scores.csv')
status_df     = pd.read_csv(f'{OUT_DIR}/player_status.csv')
roles_df      = pd.read_csv(f'{OUT_DIR}/player_role_analysis.csv')
press_df      = pd.read_csv(f'{OUT_DIR}/pressure_player_metrics.csv')
rel_df        = pd.read_csv(f'{OUT_DIR}/player_reliability.csv')
bat_df        = pd.read_csv(f'{OUT_DIR}/player_batting_metrics.csv')
bowl_df       = pd.read_csv(f'{OUT_DIR}/player_bowling_metrics.csv')
weak_df       = pd.read_csv(f'{OUT_DIR}/rr_weaknesses.csv')
comp_map      = pd.read_csv(f'{DATA_DIR}/competition_team_player_mapping.csv')
teams         = pd.read_csv(f'{DATA_DIR}/teams.csv')
pe            = pd.read_csv(f'{DATA_DIR}/playing_eleven.csv')

# Load previously verified uncapped pool
uncapped_pool = pd.read_csv(f'{OUT_DIR}/uncapped_ipl2027_candidate_pool.csv')
uncapped_pids = set(uncapped_pool['player_id'].unique())

print("--- Step 2: Categorization (Capped Indian, Uncapped Indian, Overseas) ---")
from build_uncapped_recruitment_system import all_overseas_ids, all_senior_india_capped_ids
from audit_capped_by_name import senior_india_capped_names

status_dict = status_df.drop_duplicates('player_id').set_index('player_id').to_dict('index')
roles_dict  = roles_df.drop_duplicates('player_id').set_index('player_id').to_dict('index') if not roles_df.empty else {}
press_dict  = press_df.drop_duplicates('player_id').set_index('player_id').to_dict('index') if not press_df.empty else {}
rel_dict    = rel_df.drop_duplicates('player_id').set_index('player_id').to_dict('index') if not rel_df.empty else {}

def safe_val(val, default=50.0):
    if val is None or pd.isna(val):
        return float(default)
    try:
        return float(val)
    except:
        return float(default)

# Known player ages as of late 2026
known_ages = {
    8101: 28,  # Ashutosh Sharma
    2756: 35,  # Shashank Singh
    3782: 31,  # M Shahrukh Khan
    8238: 22,  # Sameer Rizvi
    6460: 26,  # Ayush Badoni
    7059: 26,  # Nehal Wadhera
    25669: 25, # Priyansh Arya
    3926: 33,  # Rahul Tewatia
    23467: 28, # Gurjapneet Singh
    36982: 23, # Suyash Sharma
    35318: 21, # Sakib Hussain
    7327: 26,  # Rasikh Salam
    8746: 28,  # Vaibhav Arora
    27964: 25, # Anshul Kamboj
    6669: 28,  # Mohsin Khan
    8177: 32,  # Akash Madhwal
    7533: 28,  # Simarjeet Singh
    7250: 29,  # Mukesh Choudhary
    25132: 25, # Praful Hinge
    6359: 24,  # Raghu Sharma
    46137: 22, # Kartik Sharma
    45749: 23, # Mukul Choudhary
    25679: 24, # Salil Arora
    48504: 19, # Ayush Mhatre
    19714: 24, # Abishek Porel
    26906: 21, # Angkrish Raghuvanshi
    6467: 27,  # Anuj Rawat
    4821: 27,  # Mahipal Lomror
    7446: 25,  # Abdul Samad
    4494: 31,  # Abhinav Manohar
    37052: 23, # Naman Dhir
    6396: 30,  # Tim David
    3125: 31,  # Nicholas Pooran
    4260: 35,  # Heinrich Klaasen
    4708: 29,  # Rinku Singh
    781: 38,   # Sunil Narine
    7897: 23,  # Tilak Varma
    1077: 37,  # David Miller
    4391: 33,  # Liam Livingstone
    4864: 30,  # Spencer Johnson
    6628: 26,  # Gerald Coetzee
    47039: 32, # Nuwan Thushara
    7240: 26,  # Fazalhaq Farooqi
    4857: 30,  # Glenn Phillips
    4847: 28,  # Sam Curran
    4851: 26,  # Tristan Stubbs
    5041: 32,  # Mukesh Kumar
    4816: 28,  # Khaleel Ahmed
    2261: 35,  # Harshal Patel
    27960: 24, # Mayank Yadav
    3916: 33,  # Jitesh Sharma
    29888: 24, # Harshit Rana
    7544: 31,  # Venkatesh Iyer
    4823: 27,  # Washington Sundar
    4722: 28,  # Rashid Khan
    8661: 24,  # Matheesha Pathirana
    1758: 33,  # Patrick Cummins
    2367: 32,  # Travis Head
    1318: 38,  # Andre Russell
    2382: 32,  # Jamie Overton
    46066: 25, # Vipraj Nigam
    8182: 28,  # Donovan Ferreira
}

# Franchise Marquee Retentions (Impossible / extremely low probability to enter auction)
marquee_retention_ids = {
    2933, # Jasprit Bumrah (MI)
    47,   # Virat Kohli (RCB)
    126,  # Rohit Sharma (MI)
    3330, # Hardik Pandya (MI)
    6288, # Shubman Gill (GT)
    1699, # Suryakumar Yadav (MI)
    6059, # Ruturaj Gaikwad (CSK)
    2876, # Axar Patel (DC)
    3644, # Kuldeep Yadav (DC)
    8,    # MS Dhoni (CSK)
    4260, # Heinrich Klaasen (SRH)
    3125, # Nicholas Pooran (LSG)
    781,  # Sunil Narine (KKR)
    1318, # Andre Russell (KKR)
    4722, # Rashid Khan (GT)
    5810, # Rashid Khan (GT alternate ID)
    8661, # Matheesha Pathirana (CSK)
    1758, # Patrick Cummins (SRH)
    2367, # Travis Head (SRH)
}

print("--- Step 3: Computing Availability and Categorization ---")
processed_candidates = []

for idx, r in fit_df.iterrows():
    p_id = int(r['player_id'])
    p_name = str(r['player_name']).strip()
    p_name_clean = p_name.lower()
    
    # 1. Determine player category
    if p_id in all_overseas_ids:
        p_category = 'OVERSEAS'
    elif p_id in uncapped_pids:
        p_category = 'UNCAPPED_INDIAN'
    elif p_id in all_senior_india_capped_ids or p_name_clean in senior_india_capped_names:
        p_category = 'CAPPED_INDIAN'
    else:
        # Default fallback: check if Indian domestic
        p_category = 'UNCAPPED_INDIAN'
        
    # 2. Check active & retirement status
    stat_row = status_dict.get(p_id, {})
    curr_active = stat_row.get('current_active_status', r.get('current_active_status', 'UNKNOWN'))
    ret_stat    = stat_row.get('retirement_status', r.get('retirement_status', 'NOT_RETIRED'))
    final_elig  = stat_row.get('final_eligible', r.get('final_eligible', 'UNKNOWN'))
    
    # Exclude retired players
    if ret_stat == 'RETIRED' or curr_active == 'RETIRED':
        continue
        
    rr_squad_2026 = bool(r.get('rr_squad_2026', False))
    first_ipl = r.get('first_ipl_season', 2024)
    seasons_ipl = r.get('seasons_in_ipl', 1)
    
    # 3. Determine availability probability, confidence, reason, status
    if rr_squad_2026:
        avail_status = 'CURRENTLY_CONTRACTED'
        avail_prob   = 0.05
        avail_conf   = 'HIGH'
        avail_reason = 'Currently on Rajasthan Royals 2026 roster; existing internal asset, cannot be recruited externally.'
    elif p_id in marquee_retention_ids:
        avail_status = 'LIKELY_RETAINED'
        avail_prob   = 0.15
        avail_conf   = 'HIGH'
        avail_reason = 'Franchise marquee cornerstone/captain; franchise will utilize priority retention tier ahead of auction.'
    elif p_id == 8101: # Ashutosh Sharma
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.80
        avail_conf   = 'HIGH'
        avail_reason = 'Rotational impact finisher at DC/PBKS; highly likely to enter auction pool to seek frontline finisher spot.'
    elif p_id == 37052: # Naman Dhir
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.70
        avail_conf   = 'MEDIUM'
        avail_reason = 'Stuck in crowded MI middle order; strong potential auction release for purse optimization.'
    elif p_id == 6396: # Tim David
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.75
        avail_conf   = 'HIGH'
        avail_reason = 'RCB overseas slot constraints; overseas finisher entering auction pool.'
    elif p_id == 4708: # Rinku Singh
        avail_status = 'POTENTIALLY_AUCTION'
        avail_prob   = 0.50
        avail_conf   = 'MEDIUM'
        avail_reason = 'KKR retention balance dependent on domestic capped price slot.'
    elif p_id == 7897: # Tilak Varma
        avail_status = 'POTENTIALLY_AUCTION'
        avail_prob   = 0.55
        avail_conf   = 'MEDIUM'
        avail_reason = 'MI purse trade-offs across 5 senior superstars could force auction release.'
    elif p_id == 1077: # David Miller
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.80
        avail_conf   = 'HIGH'
        avail_reason = 'Overseas batter; DC expected to refresh overseas core for 2027 cycle.'
    elif p_id == 4391: # Liam Livingstone
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.75
        avail_conf   = 'HIGH'
        avail_reason = 'SRH overseas quota overflow (Klaasen, Head, Cummins); Livingstone enters auction.'
    elif p_id == 2382: # Jamie Overton
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.75
        avail_conf   = 'HIGH'
        avail_reason = 'CSK overseas bowling all-rounder; enters auction for starting XI role.'
    elif p_id == 46066: # Vipraj Nigam
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.70
        avail_conf   = 'MEDIUM'
        avail_reason = 'DC bowling all-rounder; enters auction pool.'
    elif p_id == 45749: # Mukul Choudhary
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.80
        avail_conf   = 'HIGH'
        avail_reason = 'LSG young finisher; available in auction.'
    elif p_id == 2756: # Shashank Singh
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.65
        avail_conf   = 'MEDIUM'
        avail_reason = 'PBKS uncapped retention in 2025; available if PBKS restructure uncapped allocation.'
    elif p_id == 8238: # Sameer Rizvi
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.90
        avail_conf   = 'HIGH'
        avail_reason = 'High acquisition cost led to limited playing time; prime auction entrant.'
    elif p_id == 3782: # M Shahrukh Khan
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.85
        avail_conf   = 'HIGH'
        avail_reason = 'Rotational role at GT behind frontline finishers; prime auction release.'
    elif p_id == 23467: # Gurjapneet Singh
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.85
        avail_conf   = 'HIGH'
        avail_reason = 'CSK backup left-arm pacer; entering auction pool for match opportunities.'
    elif p_id == 36982: # Suyash Sharma
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.85
        avail_conf   = 'HIGH'
        avail_reason = 'Stuck behind Narine and Varun Chakravarthy at KKR; prime auction target.'
    elif p_id == 35318: # Sakib Hussain
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.90
        avail_conf   = 'HIGH'
        avail_reason = 'Developmental express pacer entering auction for first-team exposure.'
    elif p_id == 6460: # Ayush Badoni
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.70
        avail_conf   = 'MEDIUM'
        avail_reason = 'LSG middle-order batter; potential auction entrant if LSG rebalance domestic core.'
    elif p_id == 7327: # Rasikh Salam
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.80
        avail_conf   = 'HIGH'
        avail_reason = 'Death overs specialist rotated as Impact Sub; available in auction pool.'
    elif p_id == 7059: # Nehal Wadhera
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.80
        avail_conf   = 'HIGH'
        avail_reason = 'Rotational left-hand batter at MI/PBKS seeking regular starting role.'
    elif p_id == 4864: # Spencer Johnson
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.80
        avail_conf   = 'HIGH'
        avail_reason = 'GT overseas pacer; enters auction pool as overseas pace option.'
    elif p_id == 6628: # Gerald Coetzee
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.75
        avail_conf   = 'HIGH'
        avail_reason = 'MI overseas express pacer; rotational squad asset.'
    elif p_id == 47039: # Nuwan Thushara
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.80
        avail_conf   = 'HIGH'
        avail_reason = 'Slinger death bowler; available in open auction.'
    elif p_id == 7240: # Fazalhaq Farooqi
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.85
        avail_conf   = 'HIGH'
        avail_reason = 'SRH overseas backup bowler; entering auction.'
    elif p_id == 4857: # Glenn Phillips
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.85
        avail_conf   = 'HIGH'
        avail_reason = 'SRH utility all-rounder; enters auction for starting opportunities.'
    elif p_id == 5041: # Mukesh Kumar
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.75
        avail_conf   = 'MEDIUM'
        avail_reason = 'DC pace bowler; viable auction entrant depending on retention slots.'
    elif p_id == 4816: # Khaleel Ahmed
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.75
        avail_conf   = 'MEDIUM'
        avail_reason = 'DC left-arm seamer; potential auction entrant.'
    elif p_id == 2261: # Harshal Patel
        avail_status = 'LIKELY_AUCTION'
        avail_prob   = 0.80
        avail_conf   = 'HIGH'
        avail_reason = 'PBKS death bowler / Purple Cap winner; likely auction re-entry.'
    elif p_id == 27960: # Mayank Yadav
        avail_status = 'POTENTIALLY_AUCTION'
        avail_prob   = 0.50
        avail_conf   = 'MEDIUM'
        avail_reason = 'LSG express pacer; injury management makes retention vs auction a toss-up.'
    elif p_id == 29888: # Harshit Rana
        avail_status = 'POTENTIALLY_AUCTION'
        avail_prob   = 0.55
        avail_conf   = 'MEDIUM'
        avail_reason = 'KKR young capped pacer; retention dependent on capped limit.'
    else:
        # Default realistic estimation
        if p_category == 'OVERSEAS':
            avail_status = 'LIKELY_AUCTION'
            avail_prob   = 0.75
            avail_conf   = 'MEDIUM'
            avail_reason = 'Overseas player subject to IPL 2-overseas franchise retention limits.'
        elif p_category == 'CAPPED_INDIAN':
            avail_status = 'LIKELY_AUCTION'
            avail_prob   = 0.70
            avail_conf   = 'MEDIUM'
            avail_reason = 'Domestic capped player entering auction pool.'
        else:
            avail_status = 'LIKELY_AUCTION'
            avail_prob   = 0.80
            avail_conf   = 'HIGH'
            avail_reason = 'Uncapped domestic cricketer entering open auction.'
            
    # Availability confidence score (0 to 100)
    avail_conf_score = 90.0 if avail_conf == 'HIGH' else (70.0 if avail_conf == 'MEDIUM' else 50.0)
    
    # 4. Extract roles
    det_role = r.get('determined_role', 'Specialist')
    prim_role = r.get('primary_role', det_role)
    if pd.isna(prim_role) or prim_role in ['Unknown', 'Specialist']:
        prim_role = det_role
        
    p_info = press_dict.get(p_id, {})
    r_info = rel_dict.get(p_id, {})
    role_info = roles_dict.get(p_id, {})
    
    # Identify secondary role
    if prim_role in ['Finisher', 'WK-Finisher']:
        sec_role = 'Lower-order Pace Hitter'
    elif prim_role in ['Death Bowler', 'Death bowler']:
        sec_role = 'Yorker & Slower-Ball Specialist'
    elif prim_role in ['Middle-Order Batter', 'Middle-order batter']:
        sec_role = 'Spin Destroyer / Middle Overs Striker'
    elif prim_role in ['Spinner']:
        sec_role = 'Middle-Overs Attacking Wrist Spin'
    elif prim_role in ['Pace Bowler', 'Powerplay bowler', 'Middle-over bowler']:
        sec_role = 'Hit-the-Deck Seam Bowler'
    elif 'all-rounder' in str(prim_role).lower():
        sec_role = 'Dual-Skill Tactical Utility'
    elif prim_role in ['Opener', 'Top-order batter']:
        sec_role = 'Powerplay Boundary Striker'
    else:
        sec_role = 'Tactical Specialist'
        
    # Map primary and secondary problems solved based on empirical RR weaknesses
    role_lower = (str(prim_role) + " " + str(sec_role)).lower()
    if 'finisher' in role_lower:
        prim_prob = 'HIGH_RRR_PERFORMANCE'
        sec_prob  = 'DEATH_BATTING'
    elif 'death' in role_lower:
        prim_prob = 'DEATH_BOWLING'
        sec_prob  = 'LEFT_RIGHT_MATCHUP' if ('left' in role_lower or p_id in [23467, 4864, 7240, 6669]) else 'CLOSE_MATCH_PERFORMANCE'
    elif 'spinner' in role_lower:
        prim_prob = 'SPIN_BOWLING'
        sec_prob  = 'HIGH_RRR_PERFORMANCE'
    elif 'middle' in role_lower:
        prim_prob = 'MIDDLE_ORDER_BATTING'
        sec_prob  = 'PRESSURE_BATTING'
    elif 'all-rounder' in role_lower:
        prim_prob = 'FINISHING' if 'batting' in role_lower else 'DEATH_BOWLING'
        sec_prob  = 'SPIN_BOWLING'
    elif 'opener' in role_lower or 'powerplay' in role_lower:
        prim_prob = 'POWERPLAY_BATTING' if 'batter' in role_lower or 'opener' in role_lower else 'POWERPLAY_BOWLING'
        sec_prob  = 'PRESSURE_BATTING'
    else:
        prim_prob = 'PRESSURE_BATTING'
        sec_prob  = 'PACE_DEPTH'
        
    # 5. Extract core performance metrics
    pressure_score = safe_val(r.get('pressure_score'), 50.0)
    weakness_fit   = safe_val(r.get('weakness_fit_score'), 50.0)
    role_fit       = safe_val(r.get('role_fit_score'), 50.0)
    ipl_perf       = safe_val(r.get('ipl_performance_score'), 50.0)
    recent_form    = safe_val(r.get('recent_form_score'), 50.0)
    reliability    = safe_val(r.get('reliability_score_unified'), 50.0)
    venue_fit      = safe_val(r.get('venue_fit_score'), 50.0)
    upside         = safe_val(r.get('upside_score'), 50.0)
    
    # Pressure delta
    pressure_delta = r.get('pressure_delta')
    if pd.isna(pressure_delta):
        if 'bowler' in role_lower or 'spinner' in role_lower:
            eco_delta = p_info.get('pressure_delta_economy', 0.0)
            pressure_delta = -1.0 * safe_val(eco_delta, 0.0)
        else:
            sr_delta = p_info.get('pressure_delta_SR', 0.0)
            pressure_delta = safe_val(sr_delta, 0.0)
    pressure_delta = safe_val(pressure_delta, 0.0)
    
    # Sample size (total balls faced + balls bowled)
    bf = safe_val(r.get('balls_faced'), 0.0)
    bb = safe_val(r.get('balls_bowled'), 0.0)
    sample_size = int(bf + bb)
    if sample_size == 0:
        sample_size = int(safe_val(p_info.get('pressure_balls'), 0.0) + safe_val(p_info.get('normal_balls'), 0.0))
        
    # Age
    age = known_ages.get(p_id, np.nan)
    if pd.isna(age):
        age = 24 if seasons_ipl <= 2 else (27 if seasons_ipl <= 4 else 31)
    age = int(age)
    
    # 6. Calculate FINAL_RR_2027_FIT_SCORE using exact required weights:
    # Pressure Performance: 25%
    # RR Weakness Fit: 20%
    # Role Fit: 15%
    # IPL Performance: 10%
    # Recent Performance: 10%
    # Reliability: 8%
    # Venue/Tactical Fit: 5%
    # Age/Upside: 4%
    # Availability Confidence: 3%
    final_fit_score = (
        0.25 * pressure_score +
        0.20 * weakness_fit +
        0.15 * role_fit +
        0.10 * ipl_perf +
        0.10 * recent_form +
        0.08 * reliability +
        0.05 * venue_fit +
        0.04 * upside +
        0.03 * avail_conf_score
    )
    
    # Strategic Recommendation for Recruitment
    if final_fit_score >= 72.0 and avail_prob >= 0.65:
        rec = 'PRIMARY_TARGET'
    elif final_fit_score >= 68.0 and avail_prob >= 0.60:
        rec = 'SECONDARY_TARGET'
    elif p_category == 'UNCAPPED_INDIAN' and final_fit_score >= 65.0:
        rec = 'VALUE_TARGET'
    elif upside >= 85.0 and age <= 24:
        rec = 'DEVELOPMENT_TARGET'
    elif final_fit_score >= 60.0:
        rec = 'BACKUP_TARGET'
    else:
        rec = 'AVOID' if final_fit_score < 45.0 else 'BACKUP_TARGET'
        
    # Risk factor
    if sample_size < 150:
        risk_desc = 'Sample size limitation; developmental trajectory.'
    elif age >= 33:
        risk_desc = 'Aging curve; short 1-to-2 year championship window.'
    elif avail_prob < 0.50:
        risk_desc = 'High retention competition from parent franchise.'
    elif pressure_score >= 70.0 and reliability >= 55.0:
        risk_desc = 'Low risk; proven clutch match-winner.'
    else:
        risk_desc = 'Tactical execution risk depending on pitch conditions.'
        
    processed_candidates.append({
        'player_id': p_id,
        'player_name': p_name,
        'player_category': p_category,
        'primary_role': prim_role,
        'secondary_role': sec_role,
        'current_active_status': curr_active,
        'ipl_2027_status': avail_status,
        'availability_probability': round(avail_prob, 2),
        'availability_confidence': avail_conf,
        'availability_reason': avail_reason,
        'availability_source': 'IPL 2026 Squad Tracking & Retention Policy Modeling',
        'status_date': 'November 2026',
        'rr_squad_2026': rr_squad_2026,
        'age': age,
        'pressure_score': round(pressure_score, 2),
        'pressure_delta': round(pressure_delta, 2),
        'reliability_score': round(reliability, 2),
        'sample_size': sample_size,
        'rr_weakness_fit': round(weakness_fit, 2),
        'role_fit': round(role_fit, 2),
        'ipl_performance': round(ipl_perf, 2),
        'recent_form': round(recent_form, 2),
        'venue_fit': round(venue_fit, 2),
        'age_upside': round(upside, 2),
        'final_rr_2027_fit_score': round(final_fit_score, 2),
        'primary_problem_solved': prim_prob,
        'secondary_problem_solved': sec_prob,
        'recommendation': rec,
        'risk': risk_desc
    })

all_candidates_df = pd.DataFrame(processed_candidates)
print(f"Total active eligible candidates processed: {len(all_candidates_df)}")

# ---------------------------------------------------------------------------
# Step 9A: Performance Ranking (results/ipl2027_performance_ranking.csv)
# ---------------------------------------------------------------------------
perf_df = all_candidates_df.sort_values('final_rr_2027_fit_score', ascending=False).reset_index(drop=True)
perf_df['performance_rank'] = perf_df.index + 1
perf_cols = [
    'performance_rank', 'player_id', 'player_name', 'player_category',
    'primary_role', 'secondary_role', 'final_rr_2027_fit_score',
    'pressure_score', 'pressure_delta', 'reliability_score', 'sample_size',
    'rr_weakness_fit', 'role_fit', 'ipl_performance', 'recent_form',
    'venue_fit', 'age_upside', 'primary_problem_solved', 'ipl_2027_status',
    'availability_probability'
]
perf_df[perf_cols].to_csv(f'{OUT_DIR}/ipl2027_performance_ranking.csv', index=False)
print(f"Saved: {OUT_DIR}/ipl2027_performance_ranking.csv (Rows: {len(perf_df)})")

# ---------------------------------------------------------------------------
# Step 9B: Recruitment Ranking (results/rr_ipl2027_recruitment_ranking.csv)
# ---------------------------------------------------------------------------
# Realistic external auction targets:
# - rr_squad_2026 == False
# - current_active_status == 'ACTIVE'
# - availability_probability >= 0.40 (excludes impossible marquee retentions)
# - sample_size >= 40
recruitment_df = all_candidates_df[
    (all_candidates_df['rr_squad_2026'] == False) &
    (all_candidates_df['current_active_status'] == 'ACTIVE') &
    (all_candidates_df['availability_probability'] >= 0.40) &
    (all_candidates_df['sample_size'] >= 40)
].copy()

# Sort by final_rr_2027_fit_score descending
recruitment_df = recruitment_df.sort_values('final_rr_2027_fit_score', ascending=False).reset_index(drop=True)
recruitment_df['recruitment_rank'] = recruitment_df.index + 1

rec_cols = [
    'recruitment_rank', 'player_id', 'player_name', 'player_category',
    'primary_role', 'secondary_role', 'final_rr_2027_fit_score',
    'availability_probability', 'availability_confidence', 'ipl_2027_status',
    'pressure_score', 'pressure_delta', 'reliability_score', 'sample_size',
    'rr_weakness_fit', 'role_fit', 'ipl_performance', 'recent_form',
    'venue_fit', 'age_upside', 'primary_problem_solved', 'secondary_problem_solved',
    'recommendation', 'risk', 'availability_reason'
]
recruitment_df[rec_cols].to_csv(f'{OUT_DIR}/rr_ipl2027_recruitment_ranking.csv', index=False)
print(f"Saved: {OUT_DIR}/rr_ipl2027_recruitment_ranking.csv (Rows: {len(recruitment_df)})")

# ---------------------------------------------------------------------------
# Step 10: Final Top 20 (results/rr_ipl2027_top20.csv)
# ---------------------------------------------------------------------------
top20_df = recruitment_df.head(20).copy().reset_index(drop=True)
top20_df['rank'] = top20_df.index + 1
top20_cols = [
    'rank', 'player_id', 'player_name', 'player_category',
    'primary_role', 'secondary_role', 'ipl_2027_status',
    'availability_probability', 'availability_confidence',
    'pressure_score', 'pressure_delta', 'reliability_score',
    'sample_size', 'rr_weakness_fit', 'role_fit', 'ipl_performance',
    'recent_form', 'venue_fit', 'age_upside', 'final_rr_2027_fit_score',
    'primary_problem_solved', 'recommendation', 'risk'
]
top20_df[top20_cols].to_csv(f'{OUT_DIR}/rr_ipl2027_top20.csv', index=False)
print(f"Saved: {OUT_DIR}/rr_ipl2027_top20.csv (Rows: {len(top20_df)})")

# ---------------------------------------------------------------------------
# Step 11: Separate Capped and Uncapped Results
# ---------------------------------------------------------------------------
# Capped Top 10 (CAPPED_INDIAN & OVERSEAS)
capped_pool = recruitment_df[recruitment_df['player_category'].isin(['CAPPED_INDIAN', 'OVERSEAS'])].copy()
capped_top10 = capped_pool.head(10).copy().reset_index(drop=True)
capped_top10['rank'] = capped_top10.index + 1
capped_top10[top20_cols].to_csv(f'{OUT_DIR}/rr_ipl2027_capped_top10.csv', index=False)
print(f"Saved: {OUT_DIR}/rr_ipl2027_capped_top10.csv (Rows: {len(capped_top10)})")

# Uncapped Top 10 (UNCAPPED_INDIAN)
uncapped_pool_filtered = recruitment_df[recruitment_df['player_category'] == 'UNCAPPED_INDIAN'].copy()
uncapped_top10 = uncapped_pool_filtered.head(10).copy().reset_index(drop=True)
uncapped_top10['rank'] = uncapped_top10.index + 1
uncapped_top10[top20_cols].to_csv(f'{OUT_DIR}/rr_ipl2027_uncapped_top10.csv', index=False)
print(f"Saved: {OUT_DIR}/rr_ipl2027_uncapped_top10.csv (Rows: {len(uncapped_top10)})")

# ---------------------------------------------------------------------------
# Step 12: Final Combined Top 10 (results/rr_ipl2027_final_top10.csv)
# ---------------------------------------------------------------------------
final_top10 = recruitment_df.head(10).copy().reset_index(drop=True)
final_top10['rank'] = final_top10.index + 1
final_top10[top20_cols].to_csv(f'{OUT_DIR}/rr_ipl2027_final_top10.csv', index=False)
print(f"Saved: {OUT_DIR}/rr_ipl2027_final_top10.csv (Rows: {len(final_top10)})")

# ---------------------------------------------------------------------------
# Step 13: Role-Wise Targets (results/rr_ipl2027_role_targets.csv)
# ---------------------------------------------------------------------------
def get_role_targets(problem_key, role_keywords):
    candidates = recruitment_df[
        (recruitment_df['primary_problem_solved'] == problem_key) |
        (recruitment_df['primary_role'].str.contains(role_keywords, case=False, na=False))
    ].sort_values('final_rr_2027_fit_score', ascending=False)
    
    if candidates.empty:
        return 'None', 'None', 'None', 'None'
        
    best_overall = candidates.iloc[0]['player_name']
    
    uncapped = candidates[candidates['player_category'] == 'UNCAPPED_INDIAN']
    best_uncapped = uncapped.iloc[0]['player_name'] if not uncapped.empty else 'N/A'
    
    capped = candidates[candidates['player_category'].isin(['CAPPED_INDIAN', 'OVERSEAS'])]
    best_capped = capped.iloc[0]['player_name'] if not capped.empty else 'N/A'
    
    backup = candidates.iloc[1]['player_name'] if len(candidates) > 1 else 'N/A'
    
    return best_overall, best_uncapped, best_capped, backup

role_targets_data = [
    {
        'weakness_category': 'Death Bowling',
        'rr_weakness_metric': '0.40 wkts/over vs 0.52 par (Weakness #1 & #8)',
        'best_available_target': get_role_targets('DEATH_BOWLING', 'Death|Pace')[0],
        'best_uncapped_target': get_role_targets('DEATH_BOWLING', 'Death|Pace')[1],
        'best_capped_target': get_role_targets('DEATH_BOWLING', 'Death|Pace')[2],
        'backup_target': get_role_targets('DEATH_BOWLING', 'Death|Pace')[3],
    },
    {
        'weakness_category': 'Finishing & High RRR Chasing',
        'rr_weakness_metric': '40.95% dots vs 34.47% par & 20.64% death boundary (Weakness #2 & #3)',
        'best_available_target': get_role_targets('HIGH_RRR_PERFORMANCE', 'Finisher')[0],
        'best_uncapped_target': get_role_targets('HIGH_RRR_PERFORMANCE', 'Finisher')[1],
        'best_capped_target': get_role_targets('HIGH_RRR_PERFORMANCE', 'Finisher')[2],
        'backup_target': get_role_targets('HIGH_RRR_PERFORMANCE', 'Finisher')[3],
    },
    {
        'weakness_category': 'Middle-Order Batting vs Spin',
        'rr_weakness_metric': '31.67% middle dots vs 29.53% par (Weakness #7)',
        'best_available_target': get_role_targets('MIDDLE_ORDER_BATTING', 'Middle-order|Middle-Order')[0],
        'best_uncapped_target': get_role_targets('MIDDLE_ORDER_BATTING', 'Middle-order|Middle-Order')[1],
        'best_capped_target': get_role_targets('MIDDLE_ORDER_BATTING', 'Middle-order|Middle-Order')[2],
        'backup_target': get_role_targets('MIDDLE_ORDER_BATTING', 'Middle-order|Middle-Order')[3],
    },
    {
        'weakness_category': 'Attacking Spin & High RRR Bowling',
        'rr_weakness_metric': '0.33 wkts/over vs 0.38 par under High RRR (Weakness #4)',
        'best_available_target': get_role_targets('SPIN_BOWLING', 'Spinner|Spin')[0],
        'best_uncapped_target': get_role_targets('SPIN_BOWLING', 'Spinner|Spin')[1],
        'best_capped_target': get_role_targets('SPIN_BOWLING', 'Spinner|Spin')[2],
        'backup_target': get_role_targets('SPIN_BOWLING', 'Spinner|Spin')[3],
    },
    {
        'weakness_category': 'Bowling vs Left-Handed Batters',
        'rr_weakness_metric': '10.28 economy vs 9.60 par & 26.56% boundaries (Weakness #5 & #9)',
        'best_available_target': 'Gurjapneet Singh (Left-Arm)',
        'best_uncapped_target': 'Gurjapneet Singh (Left-Arm)',
        'best_capped_target': 'Spencer Johnson (Left-Arm)',
        'backup_target': 'Fazalhaq Farooqi (Left-Arm)',
    },
    {
        'weakness_category': 'Powerplay Bowling Seam Penetration',
        'rr_weakness_metric': '27.38% boundary vs 26.74% par (Weakness #14)',
        'best_available_target': 'Deepak Chahar',
        'best_uncapped_target': 'Vaibhav Arora',
        'best_capped_target': 'Deepak Chahar',
        'backup_target': 'Harshal Patel',
    }
]

role_targets_df = pd.DataFrame(role_targets_data)
role_targets_df.to_csv(f'{OUT_DIR}/rr_ipl2027_role_targets.csv', index=False)
print(f"Saved: {OUT_DIR}/rr_ipl2027_role_targets.csv")

# ---------------------------------------------------------------------------
# Step 14: Value vs Upside Matrix (results/rr_ipl2027_value_upside_matrix.csv)
# ---------------------------------------------------------------------------
matrix_rows = []
for idx, r in recruitment_df.head(50).iterrows():
    curr_high = r['final_rr_2027_fit_score'] >= 68.0
    upside_high = r['age_upside'] >= 80.0
    
    if curr_high and upside_high:
        quad = 'HIGH_CURRENT / HIGH_UPSIDE'
        strat = 'TIER-1 PRIORITY TARGET (Aggressive bidding up to 7 Cr)'
    elif curr_high and not upside_high:
        quad = 'HIGH_CURRENT / LOW_UPSIDE'
        strat = 'WIN-NOW IMPACT VETERAN (1-2 Year tactical window, 3-5 Cr)'
    elif not curr_high and upside_high:
        quad = 'LOW_CURRENT / HIGH_UPSIDE'
        strat = 'DEVELOPMENTAL VALUE (Steal at base price / <1.5 Cr)'
    else:
        quad = 'LOW_CURRENT / LOW_UPSIDE'
        strat = 'SQUAD DEPTH / BACKUP (Base price acquisition)'
        
    matrix_rows.append({
        'player_id': r['player_id'],
        'player_name': r['player_name'],
        'player_category': r['player_category'],
        'primary_role': r['primary_role'],
        'age': r['age'],
        'final_rr_2027_fit_score': r['final_rr_2027_fit_score'],
        'age_upside': r['age_upside'],
        'availability_probability': r['availability_probability'],
        'quadrant': quad,
        'auction_strategy': strat
    })

matrix_df = pd.DataFrame(matrix_rows)
matrix_df.to_csv(f'{OUT_DIR}/rr_ipl2027_value_upside_matrix.csv', index=False)
print(f"Saved: {OUT_DIR}/rr_ipl2027_value_upside_matrix.csv")

print("\n--- FINAL COMBINED TOP 10 PREVIEW ---")
for idx, r in final_top10.iterrows():
    print(f"#{r['rank']:2d}: {r['player_name']:<22} | {r['player_category']:<15} | Role: {r['primary_role']:<20} | Score: {r['final_rr_2027_fit_score']:.2f} | Pressure: {r['pressure_score']:.1f} | Avail: {r['availability_probability']:.2f} | Rec: {r['recommendation']}")
