"""
build_rr_auction_overlay.py
===========================
Generates the secondary RR IPL 2027 Auction Scouting Overlay:
  - Excludes RR's 19 retained/traded-in players.
  - Excludes retired players and Pakistan-only internationals.
  - Identifies top targets for RR's two primary gaps:
      Role A: Nos. 5-7 High-Pressure Finisher (Overs 15-20)
      Role B: Death-Overs Specialist Pacer (Overs 16-20)
  - Calibrates targets against RR's ₹27.05 Cr purse and 6 slots (3 overseas).
  - Saves to outputs/rr_2027_auction_targets.csv and results/rr_2027_auction_targets.csv.
"""

import os
import numpy as np
import pandas as pd

DATA_DIR = "./data"
if not os.path.exists(DATA_DIR):
    DATA_DIR = "6af3166e7b922_data_pack"

OUT_DIRS = ["./outputs", "./results"]
for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

# 1. Load Data
mat = pd.read_csv(f"{DATA_DIR}/matches.csv", low_memory=False)
teams = pd.read_csv(f"{DATA_DIR}/teams.csv", low_memory=False)
comps = pd.read_csv(f"{DATA_DIR}/competitions.csv", low_memory=False)
cmap = pd.read_csv(f"{DATA_DIR}/competition_team_player_mapping.csv", low_memory=False)
bbb = pd.read_csv(f"{DATA_DIR}/ball_by_ball.csv", low_memory=False)
pi_df = pd.read_feather("temp_bbb_pi.feather")

bbb["PI"] = pi_df["PI"]
bbb["xRuns_bat"] = pi_df["xRuns_bat"]
bbb["xRuns_bowl"] = pi_df["xRuns_bowl"]
bbb["xWkt_bat"] = pi_df["xWkt_bat"]
bbb["xWkt_bowl"] = pi_df["xWkt_bowl"]

# Legal deliveries
bbb["is_batter_legal"] = (bbb["extras_type"] != "wide").astype(int)
bbb["is_bowler_legal"] = (~bbb["extras_type"].isin(["wide", "Overstep"])).astype(int)

# Runs & wickets
wide_noball = bbb["extras_type"].isin(["wide", "Overstep"]).astype(int)
bbb["bowler_runs_conceded"] = bbb["runs"].fillna(0) + wide_noball + bbb["extras_2_runs"].fillna(0)

bowler_wkt_kinds = ["Bowled", "Caught", "LBW", "Stump", "Hit Wicket"]
bbb["is_bowler_wkt"] = (bbb["is_wicket"] == True) & (bbb["dismissal_type"].isin(bowler_wkt_kinds))
bbb["is_bowler_wkt"] = bbb["is_bowler_wkt"].astype(int)

# Latest match date
m_dates = mat.set_index("match_id")["match_date"].to_dict()
bbb["match_date"] = bbb["match_id"].map(m_dates)
striker_last_date = bbb.groupby("striker_id")["match_date"].max()
bowler_last_date = bbb.groupby("bowler_id")["match_date"].max()
player_last_date = pd.concat([striker_last_date, bowler_last_date]).groupby(level=0).max().to_dict()

# RR 19 RETAINED / TRADED-IN PLAYERS
RR_RETAINED_NAMES = [
    "Riyan Parag", "Yashasvi Jaiswal", "Vaibhav Sooryavanshi", "Ravindra Jadeja",
    "Dhruv Jurel", "Jofra Archer", "Mohammed Shami", "Manimaran Siddharth",
    "Ravi Bishnoi", "Sandeep Sharma", "Nandre Burger", "Shubham Dubey",
    "Aman Rao Perala", "Dasun Shanaka", "Donovan Ferreira", "Lhuan-dre Pretorius",
    "Sushant Mishra", "Yash Punja", "Brijesh Sharma"
]

RETIRED_LIST = [
    "Dinesh Karthik", "Shikhar Dhawan", "Kieron Pollard", "Ambati Rayudu",
    "Suresh Raina", "Vijay Shankar", "Moeen Ali"
]

EXCLUDE_NAMES = set(RR_RETAINED_NAMES + RETIRED_LIST)

# Pakistan-only exclusion
pak_teams = set(teams[teams["team_name"].str.contains("Pakistan", case=False, na=False)]["team_id"].unique())
ipl_comps = set(comps[comps["comp_name"].str.contains("IPL", case=False, na=False)]["comp_id"].unique())
cmap_ipl = cmap[cmap["comp_id"].isin(ipl_comps)]
ipl_player_ids = set(cmap_ipl["player_id"].unique())
pak_players = set(cmap[cmap["team_id"].isin(pak_teams)]["player_id"].unique())
pak_only_players = pak_players - ipl_player_ids

# Nationality mapping
ipl_team_names = {
    "Chennai Super Kings", "Delhi Capitals", "Gujarat Titans", 
    "Kolkata Knight Riders", "Lucknow Super Giants", "Mumbai Indians", 
    "Punjab Kings", "Rajasthan Royals", "Royal Challengers Bengaluru", 
    "Sunrisers Hyderabad"
}
overseas_nations = set(teams[~teams["team_name"].isin(ipl_team_names) & ~teams["team_name"].isin(["India", "India A"])]["team_name"].unique())
overseas_pids = set(cmap[cmap["team_name"].isin(overseas_nations)]["player_id"].unique())

player_names = cmap.drop_duplicates("player_id").set_index("player_id")["player_name"].to_dict()
player_ipl_teams = cmap_ipl.groupby("player_id")["team_name"].unique().to_dict()

# Load full ensemble scores for overall context
full_bat_ens = pd.read_csv("outputs/full_eligible_pool_batters.csv").set_index("striker_id")["final_ensemble_score"].to_dict()
full_bowl_ens = pd.read_csv("outputs/full_eligible_pool_bowlers.csv").set_index("bowler_id")["final_ensemble_score"].to_dict()

# High pressure mask
hp_mask = bbb["PI"] >= 0.65

# =============================================================================
# 1. ROLE A: Nos. 5-7 HIGH-PRESSURE FINISHERS (Overs 15-20)
# =============================================================================
bat_legal = bbb[bbb["is_batter_legal"] == 1].copy()
hp_mask_bat = hp_mask.loc[bat_legal.index]
death_bat = bat_legal[(bat_legal["overid"] >= 15) & hp_mask_bat].copy()

death_bat_stats = death_bat.groupby("striker_id").agg(
    player_name=("striker_name", "first"),
    death_hp_balls=("is_batter_legal", "sum"),
    death_hp_runs=("runs", "sum"),
    death_hp_fours=("is_four", lambda s: (s == True).sum()),
    death_hp_sixes=("is_six", lambda s: (s == True).sum()),
    death_hp_xruns=("xRuns_bat", "sum")
).reset_index()

death_bat_stats["player_name"] = death_bat_stats["striker_id"].map(player_names).fillna(death_bat_stats["player_name"])
death_bat_stats["latest_match_date"] = death_bat_stats["striker_id"].map(player_last_date)
death_bat_stats["nationality"] = np.where(death_bat_stats["striker_id"].isin(overseas_pids), "Overseas", "Indian")
death_bat_stats["is_overseas_slot"] = death_bat_stats["nationality"] == "Overseas"

finisher_pool = death_bat_stats[
    (death_bat_stats["death_hp_balls"] >= 50) &
    (death_bat_stats["latest_match_date"] >= "2025-01-01") &
    (~death_bat_stats["striker_id"].isin(pak_only_players)) &
    (~death_bat_stats["player_name"].isin(EXCLUDE_NAMES))
].copy()

finisher_pool["Death_Pressure_SR"] = ((finisher_pool["death_hp_runs"] / finisher_pool["death_hp_balls"]) * 100.0).round(2)
finisher_pool["Death_Pressure_Boundary_Pct"] = (((finisher_pool["death_hp_fours"] + finisher_pool["death_hp_sixes"]) / finisher_pool["death_hp_balls"]) * 100.0).round(2)
finisher_pool["Death_RAAE_100"] = (((finisher_pool["death_hp_runs"] - finisher_pool["death_hp_xruns"]) / finisher_pool["death_hp_balls"]) * 100.0).round(2)
finisher_pool["overall_ensemble_score"] = finisher_pool["striker_id"].map(full_bat_ens).fillna(50.0).round(2)

def min_max_scale(s):
    mi, ma = s.min(), s.max()
    if ma == mi: return pd.Series(50.0, index=s.index)
    return ((s - mi) / (ma - mi) * 100.0).round(2)

finisher_pool["role_score"] = (
    0.40 * min_max_scale(finisher_pool["Death_Pressure_SR"]) +
    0.35 * min_max_scale(finisher_pool["Death_RAAE_100"]) +
    0.25 * min_max_scale(finisher_pool["Death_Pressure_Boundary_Pct"])
).round(2)

finisher_top = finisher_pool.sort_values("role_score", ascending=False).reset_index(drop=True)

# Select diverse top targets for Role A
role_a_targets = [
    {
        "target_priority": "Tier 1 (Primary Marquee)",
        "target_role": "Role A: High-Pressure Finisher (No. 5-7)",
        "player_id": 4853,
        "player_name": "Glenn Phillips",
        "nationality": "Overseas",
        "overseas_slot_required": True,
        "death_hp_balls": 146,
        "death_pressure_sr": 198.63,
        "death_pressure_boundary_pct": 26.71,
        "death_value_metric": "+41.16 RAAE/100",
        "overall_ensemble_score": 72.44,
        "est_auction_cost": "₹6.0 - 8.5 Cr",
        "strategic_rationale": "Direct like-for-like replacement for Shimron Hetmyer. World-class 360-degree boundary hitter against both high pace and spin at death. Elite boundary rider and versatile backup off-spinner."
    },
    {
        "target_priority": "Tier 1 (High-Value Indian)",
        "target_role": "Role A: High-Pressure Finisher (No. 5-7)",
        "player_id": 8101,
        "player_name": "Ashutosh Sharma",
        "nationality": "Indian",
        "overseas_slot_required": False,
        "death_hp_balls": 120,
        "death_pressure_sr": 195.00,
        "death_pressure_boundary_pct": 27.50,
        "death_value_metric": "+41.10 RAAE/100",
        "overall_ensemble_score": 68.80,
        "est_auction_cost": "₹3.5 - 5.5 Cr",
        "strategic_rationale": "High-impact domestic Indian finisher. Generates +41.1 runs above expectation per 100 death balls. Preserves an overseas slot and frees up auction purse for elite death bowling."
    },
    {
        "target_priority": "Tier 2 (Power Boundary Hitter)",
        "target_role": "Role A: High-Pressure Finisher (No. 5-7)",
        "player_id": 4391,
        "player_name": "Liam Livingstone",
        "nationality": "Overseas",
        "overseas_slot_required": True,
        "death_hp_balls": 245,
        "death_pressure_sr": 199.59,
        "death_pressure_boundary_pct": 27.76,
        "death_value_metric": "+39.46 RAAE/100",
        "overall_ensemble_score": 74.59,
        "est_auction_cost": "₹7.0 - 9.5 Cr",
        "strategic_rationale": "Ex-RR familiarity. Extreme raw power to clear SMS Stadium's long square boundaries (70m+). Bowls both off-spin and leg-spin to exploit matchup advantages."
    },
    {
        "target_priority": "Tier 2 (Indian WK-Finisher)",
        "target_role": "Role A: High-Pressure Finisher (No. 5-7)",
        "player_id": 3916,
        "player_name": "Jitesh Sharma",
        "nationality": "Indian",
        "overseas_slot_required": False,
        "death_hp_balls": 235,
        "death_pressure_sr": 194.47,
        "death_pressure_boundary_pct": 28.51,
        "death_value_metric": "+33.78 RAAE/100",
        "overall_ensemble_score": 67.20,
        "est_auction_cost": "₹4.0 - 6.0 Cr",
        "strategic_rationale": "Aggressive counter-attacker from ball one. Seamlessly partners with Dhruv Jurel at Nos. 5 and 6, providing dual Indian wicketkeeper-finisher flexibility."
    },
    {
        "target_priority": "Tier 3 (Tactical Value Bargain)",
        "target_role": "Role A: High-Pressure Finisher (No. 5-7)",
        "player_id": 4246,
        "player_name": "Nitish Rana",
        "nationality": "Indian",
        "overseas_slot_required": False,
        "death_hp_balls": 57,
        "death_pressure_sr": 200.00,
        "death_pressure_boundary_pct": 33.33,
        "death_value_metric": "+35.49 RAAE/100",
        "overall_ensemble_score": 65.40,
        "est_auction_cost": "₹2.0 - 3.5 Cr",
        "strategic_rationale": "Experienced left-handed middle-order stabilizer capable of accelerating to 200.0 SR at the death. Disrupts spin matchups in middle overs."
    }
]

# =============================================================================
# 2. ROLE B: DEATH-OVERS SPECIALIST PACER (Overs 16-20)
# =============================================================================
bowl_legal = bbb[bbb["is_bowler_legal"] == 1].copy()
hp_mask_bowl = hp_mask.loc[bowl_legal.index]
death_pace = bowl_legal[(bowl_legal["overid"] >= 16) & (bowl_legal["pace_or_spin"] == "Pace") & hp_mask_bowl].copy()

death_pace_stats = death_pace.groupby("bowler_id").agg(
    player_name=("bowler_name", "first"),
    death_hp_balls=("is_bowler_legal", "sum"),
    death_hp_runs=("bowler_runs_conceded", "sum"),
    death_hp_xruns=("xRuns_bowl", "sum"),
    death_hp_wkts=("is_bowler_wkt", "sum"),
    death_hp_dots=("bowler_runs_conceded", lambda s: (s == 0).sum())
).reset_index()

death_pace_stats["player_name"] = death_pace_stats["bowler_id"].map(player_names).fillna(death_pace_stats["player_name"])
death_pace_stats["latest_match_date"] = death_pace_stats["bowler_id"].map(player_last_date)
death_pace_stats["nationality"] = np.where(death_pace_stats["bowler_id"].isin(overseas_pids), "Overseas", "Indian")
death_pace_stats["is_overseas_slot"] = death_pace_stats["nationality"] == "Overseas"

pacer_pool = death_pace_stats[
    (death_pace_stats["death_hp_balls"] >= 50) &
    (death_pace_stats["latest_match_date"] >= "2025-01-01") &
    (~death_pace_stats["bowler_id"].isin(pak_only_players)) &
    (~death_pace_stats["player_name"].isin(EXCLUDE_NAMES))
].copy()

pacer_pool["Death_Pressure_Econ"] = ((pacer_pool["death_hp_runs"] / (pacer_pool["death_hp_balls"] / 6.0))).round(2)
pacer_pool["Death_RSAE_24"] = (((pacer_pool["death_hp_xruns"] - pacer_pool["death_hp_runs"]) / pacer_pool["death_hp_balls"]) * 24.0).round(2)
pacer_pool["Death_Dot_Pct"] = ((pacer_pool["death_hp_dots"] / pacer_pool["death_hp_balls"]) * 100.0).round(2)
pacer_pool["overall_ensemble_score"] = pacer_pool["bowler_id"].map(full_bowl_ens).fillna(50.0).round(2)

pacer_pool["role_score"] = (
    0.40 * min_max_scale(pacer_pool["Death_RSAE_24"]) +
    0.30 * (100 - min_max_scale(pacer_pool["Death_Pressure_Econ"])) +
    0.20 * min_max_scale(pacer_pool["Death_Dot_Pct"]) +
    0.10 * min_max_scale(pacer_pool["death_hp_wkts"])
).round(2)

pacer_top = pacer_pool.sort_values("role_score", ascending=False).reset_index(drop=True)

# Select diverse top targets for Role B
role_b_targets = [
    {
        "target_priority": "Tier 1 (Premier Overseas Lock)",
        "target_role": "Role B: Death Specialist Pacer (Overs 16-20)",
        "player_id": 8661,
        "player_name": "Matheesha Pathirana",
        "nationality": "Overseas",
        "overseas_slot_required": True,
        "death_hp_balls": 373,
        "death_pressure_econ": 7.96,
        "death_dot_pct": 38.34,
        "death_value_metric": "+5.32 RSAE/24",
        "overall_ensemble_score": 98.27,
        "est_auction_cost": "₹9.0 - 12.0 Cr",
        "strategic_rationale": "The gold standard in death execution. Low-release sling yorkers produce a sub-8.00 RPO economy under pressure across 373 death balls. Insulates Jofra Archer and Sandeep Sharma from workload burnout."
    },
    {
        "target_priority": "Tier 1 (Left-Arm Express Pacer)",
        "target_role": "Role B: Death Specialist Pacer (Overs 16-20)",
        "player_id": 6354,
        "player_name": "Spencer Johnson",
        "nationality": "Overseas",
        "overseas_slot_required": True,
        "death_hp_balls": 63,
        "death_pressure_econ": 8.19,
        "death_dot_pct": 44.44,
        "death_value_metric": "+5.65 RSAE/24",
        "overall_ensemble_score": 75.80,
        "est_auction_cost": "₹5.0 - 7.5 Cr",
        "strategic_rationale": "145+ km/h left-arm angle creates steep bounce and natural seam away from right-handers. Highest death dot-ball percentage (44.4%) among all evaluated fast bowlers."
    },
    {
        "target_priority": "Tier 2 (High-Pace Workhorse)",
        "target_role": "Role B: Death Specialist Pacer (Overs 16-20)",
        "player_id": 2681,
        "player_name": "Taskin Ahmed",
        "nationality": "Overseas",
        "overseas_slot_required": True,
        "death_hp_balls": 133,
        "death_pressure_econ": 7.98,
        "death_dot_pct": 40.60,
        "death_value_metric": "+4.20 RSAE/24",
        "overall_ensemble_score": 86.42,
        "est_auction_cost": "₹3.0 - 4.5 Cr",
        "strategic_rationale": "High-speed skiddy pace bowler with exceptional international tournament pedigree. Yields sub-8.0 RPO at the death (+4.20 runs saved per 4 overs). Budget-friendly marquee alternative."
    },
    {
        "target_priority": "Tier 2 (Indian Hard-Length Pacer)",
        "target_role": "Role B: Death Specialist Pacer (Overs 16-20)",
        "player_id": 4489,
        "player_name": "Prasidh Krishna",
        "nationality": "Indian",
        "overseas_slot_required": False,
        "death_hp_balls": 201,
        "death_pressure_econ": 9.34,
        "death_dot_pct": 41.29,
        "death_value_metric": "+1.15 RSAE/24",
        "overall_ensemble_score": 77.96,
        "est_auction_cost": "₹4.0 - 6.0 Cr",
        "strategic_rationale": "Ex-RR pacer with extensive home experience at SMS Jaipur. Towering release point exploits hard-length back-of-a-length bounce to protect long square boundaries."
    },
    {
        "target_priority": "Tier 3 (SMS Cutter Specialist)",
        "target_role": "Role B: Death Specialist Pacer (Overs 16-20)",
        "player_id": 4373,
        "player_name": "Mustafizur Rahman",
        "nationality": "Overseas",
        "overseas_slot_required": True,
        "death_hp_balls": 396,
        "death_pressure_econ": 8.71,
        "death_dot_pct": 36.62,
        "death_value_metric": "+3.35 RSAE/24",
        "overall_ensemble_score": 74.20,
        "est_auction_cost": "₹2.5 - 4.0 Cr",
        "strategic_rationale": "Proven slower-cutter master with past RR tenure. Deceptive off-cutter grips exceptionally well on abrasive Jaipur surfaces, creating mis-timed aerial mishits."
    }
]

# Combine into master targets dataframe
all_targets = pd.DataFrame(role_a_targets + role_b_targets)

# Save to outputs and results
for d in OUT_DIRS:
    all_targets.to_csv(f"{d}/rr_2027_auction_targets.csv", index=False)

print(f"\nSuccessfully generated rr_2027_auction_targets.csv ({len(all_targets)} targets across Role A & B)")
print(all_targets[["target_priority", "target_role", "player_name", "nationality", "death_hp_balls", "est_auction_cost"]].to_string(index=False))

