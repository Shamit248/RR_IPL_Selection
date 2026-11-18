"""
build_final_ensemble_rankings.py
================================
Final Ensemble Aggregation with IPL-Eligibility & Active-Player Filters
for Rajasthan Royals SupeRR Selector Season 2 (Round 1).

Executes:
  1. Relational join & match-state reconstruction across reference CSVs.
  2. Strict filtering:
     - Excludes Pakistan-only internationals (in Pakistan squad, no IPL mapping).
     - Excludes inactive/retired players (last match date prior to 2025-01-01).
     - Configurable RETIRED_EXCLUSION_LIST for manual overrides.
     - Sample size cutoff: >= 120 legal high-pressure deliveries (PI >= 0.65).
  3. Evaluates 3 distinct pressure modeling paradigms:
     - Model 1: Contextual Machine Learning Expectation Model (RAAE/100 & RSAE/24 + Wicket Factor)
     - Model 2: Rate Elevation & Baseline Delta Model (Delta SR & Delta Economy)
     - Model 3: Clutch Match Consistency & Reliability Model (Match-level win-rate under pressure)
  4. Standardizes models using Z-scores across the eligible pool.
  5. Computes:
     - Weighted Z-Score Ensemble (M1: 0.40, M2: 0.35, M3: 0.25)
     - Equal-Weight Z-Score Ensemble (1/3 each)
     - Reciprocal Rank Fusion (RRF): sum(1 / (10 + rank))
     - Final Ensemble Score (scaled 0 to 100)
  6. Computes Spearman Rank Correlation Matrix.
  7. Outputs publication-ready Top 15 Batters and Top 15 Bowlers tables with Ranks 11-15 as backups.
"""

import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, zscore

# Paths
DATA_DIR = "./data"
if not os.path.exists(DATA_DIR):
    DATA_DIR = "6af3166e7b922_data_pack"

OUT_DIRS = ["./outputs", "./results"]
for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

print("=" * 70)
print("1. LOADING REFERENCE CSVS & MATCH METADATA")
print("=" * 70)

mat   = pd.read_csv(f"{DATA_DIR}/matches.csv", low_memory=False)
teams = pd.read_csv(f"{DATA_DIR}/teams.csv", low_memory=False)
comps = pd.read_csv(f"{DATA_DIR}/competitions.csv", low_memory=False)
cmap  = pd.read_csv(f"{DATA_DIR}/competition_team_player_mapping.csv", low_memory=False)
bbb   = pd.read_csv(f"{DATA_DIR}/ball_by_ball.csv", low_memory=False)

# Load precomputed high-fidelity PI & contextual expectations if available
pi_feather = "temp_bbb_pi.feather"
if os.path.exists(pi_feather):
    pi_df = pd.read_feather(pi_feather)
    bbb["PI"] = pi_df["PI"]
    bbb["xRuns_bat"] = pi_df["xRuns_bat"]
    bbb["xRuns_bowl"] = pi_df["xRuns_bowl"]
    bbb["xWkt_bat"] = pi_df["xWkt_bat"]
    bbb["xWkt_bowl"] = pi_df["xWkt_bowl"]
    print(f"Loaded {len(pi_df):,} delivery expectations from {pi_feather}.")
else:
    raise FileNotFoundError(f"{pi_feather} is required for contextual expectations.")

# Match dates and team mappings
m_dates = mat.set_index("match_id")["match_date"].to_dict()
bbb["match_date"] = bbb["match_id"].map(m_dates)

# Legal balls
bbb["is_batter_legal"] = (bbb["extras_type"] != "wide").astype(int)
bbb["is_bowler_legal"] = (~bbb["extras_type"].isin(["wide", "Overstep"])).astype(int)

# Runs and wickets accounting
wide_noball = bbb["extras_type"].isin(["wide", "Overstep"]).astype(int)
bbb["bowler_runs_conceded"] = bbb["runs"].fillna(0) + wide_noball + bbb["extras_2_runs"].fillna(0)

bowler_wkt_kinds = ["Bowled", "Caught", "LBW", "Stump", "Hit Wicket"]
bbb["is_bowler_wkt"] = (bbb["is_wicket"] == True) & (bbb["dismissal_type"].isin(bowler_wkt_kinds))
bbb["is_bowler_wkt"] = bbb["is_bowler_wkt"].astype(int)

striker_out = (bbb["is_wicket"] == True) & (
    (bbb["dismissal_type"] != "RunOut") | (bbb["dismissed_player_id"] == bbb["striker_id"])
)
bbb["is_striker_out"] = striker_out.astype(int)

# IPL teams mapping
ipl_comps = set(comps[comps["comp_name"].str.contains("IPL", case=False, na=False)]["comp_id"].unique())
cmap_ipl = cmap[cmap["comp_id"].isin(ipl_comps)]
player_ipl_teams = cmap_ipl.groupby("player_id")["team_name"].unique().to_dict()
player_all_teams = cmap.groupby("player_id")["team_name"].unique().to_dict()
player_names = cmap.drop_duplicates("player_id").set_index("player_id")["player_name"].to_dict()

print("\n" + "=" * 70)
print("2. APPLYING IPL-ELIGIBILITY & ACTIVE-PLAYER FILTERS")
print("=" * 70)

# 1. Exclude Pakistan-only internationals
pak_teams = set(teams[teams["team_name"].str.contains("Pakistan", case=False, na=False)]["team_id"].unique())
pak_players = set(cmap[cmap["team_id"].isin(pak_teams)]["player_id"].unique())
ipl_player_ids = set(cmap_ipl["player_id"].unique())
pak_only_players = pak_players - ipl_player_ids

print(f"Total players associated with Pakistan: {len(pak_players)}")
print(f"Pakistan players with IPL mapping: {len(pak_players & ipl_player_ids)}")
print(f"Pakistan-only players EXCLUDED: {len(pak_only_players)}")

# 2. Exclude Inactive / Retired Players (last match date in dataset prior to 2025-01-01)
striker_last_date = bbb.groupby("striker_id")["match_date"].max()
bowler_last_date = bbb.groupby("bowler_id")["match_date"].max()
player_last_date = pd.concat([striker_last_date, bowler_last_date]).groupby(level=0).max().to_dict()

active_cutoff = "2025-01-01"
active_players = {pid for pid, d in player_last_date.items() if str(d) >= active_cutoff}
inactive_players = {pid for pid, d in player_last_date.items() if str(d) < active_cutoff}

print(f"Active players (last match >= {active_cutoff}): {len(active_players)}")
print(f"Inactive players (last match < {active_cutoff}) EXCLUDED: {len(inactive_players)}")

# Configurable RETIRED_EXCLUSION_LIST (by player_id or exact player_name)
RETIRED_EXCLUSION_LIST = [
    "Dinesh Karthik",
    "Shikhar Dhawan",
    "Kieron Pollard",
    "Ambati Rayudu",
    "Suresh Raina",
    "Vijay Shankar",
    "Moeen Ali",
]
retired_pids = set(cmap[cmap["player_name"].isin(RETIRED_EXCLUSION_LIST)]["player_id"].unique())
retired_pids.update([2877, 1596])  # Explicitly add Vijay Shankar and Moeen Ali IDs
print(f"Manual retired exclusion list: {RETIRED_EXCLUSION_LIST} ({len(retired_pids)} IDs excluded)")

# 3. High-Pressure definition (PI >= 0.65)
hp_mask = bbb["PI"] >= 0.65
print(f"High-pressure deliveries (PI >= 0.65): {hp_mask.sum():,} ({hp_mask.mean()*100:.2f}% of dataset)")

# =============================================================================
# 3. BATTING MODELS & ENSEMBLE
# =============================================================================
print("\n" + "=" * 70)
print("3. MODELING BATTERS UNDER PRESSURE")
print("=" * 70)

bat_legal = bbb[bbb["is_batter_legal"] == 1].copy()
hp_mask_bat = hp_mask.loc[bat_legal.index]

hp_bat = bat_legal[hp_mask_bat].groupby("striker_id").agg(
    player_name=("striker_name", "first"),
    hp_matches=("match_id", "nunique"),
    hp_balls=("is_batter_legal", "sum"),
    hp_runs=("runs", "sum"),
    hp_xruns=("xRuns_bat", "sum"),
    hp_outs=("is_striker_out", "sum"),
    hp_xwkt=("xWkt_bat", "sum"),
    hp_fours=("is_four", lambda s: (s == True).sum()),
    hp_sixes=("is_six", lambda s: (s == True).sum()),
    hp_dots=("runs", lambda s: (s == 0).sum())
).reset_index()

us_bat = bat_legal[~hp_mask_bat].groupby("striker_id").agg(
    us_matches=("match_id", "nunique"),
    us_balls=("is_batter_legal", "sum"),
    us_runs=("runs", "sum"),
    us_outs=("is_striker_out", "sum")
).reset_index()

bat_df = hp_bat.merge(us_bat, on="striker_id", how="left")
bat_df["latest_match_date"] = bat_df["striker_id"].map(player_last_date)
bat_df["player_name"] = bat_df["striker_id"].map(player_names).fillna(bat_df["player_name"])

# Apply filters
bat_elig = bat_df[
    (bat_df["hp_balls"] >= 120) &
    (bat_df["striker_id"].isin(active_players)) &
    (~bat_df["striker_id"].isin(pak_only_players)) &
    (~bat_df["striker_id"].isin(retired_pids)) &
    (~bat_df["player_name"].isin(RETIRED_EXCLUSION_LIST))
].copy()

print(f"Qualified Batters meeting all filters (>=120 HP balls, active, non-Pak): {len(bat_elig)}")

# Batting core metrics
bat_elig["Pressure_SR"] = (bat_elig["hp_runs"] / bat_elig["hp_balls"]) * 100.0
bat_elig["Usual_SR"] = np.where(bat_elig["us_balls"] >= 20, (bat_elig["us_runs"] / bat_elig["us_balls"]) * 100.0, np.nan)
bat_elig["Delta_SR"] = bat_elig["Pressure_SR"] - bat_elig["Usual_SR"]
bat_elig["Raw_RAA_100"] = ((bat_elig["hp_runs"] - bat_elig["hp_xruns"]) / bat_elig["hp_balls"]) * 100.0
bat_elig["Wicket_Preservation"] = bat_elig["hp_xwkt"] / bat_elig["hp_outs"].clip(lower=1)

# Match-level consistency for batters
hp_match_bat = bat_legal[hp_mask_bat].groupby(["striker_id", "match_id"]).agg(
    m_balls=("is_batter_legal", "sum"),
    m_runs=("runs", "sum"),
    m_xruns=("xRuns_bat", "sum")
).reset_index()
hp_match_bat = hp_match_bat[hp_match_bat["m_balls"] >= 5]
hp_match_bat["pos_impact"] = hp_match_bat["m_runs"] > hp_match_bat["m_xruns"]

bat_cons = hp_match_bat.groupby("striker_id").agg(
    eval_matches=("pos_impact", "count"),
    pos_matches=("pos_impact", "sum")
).reset_index()
bat_cons["Consistency_Pct"] = (bat_cons["pos_matches"] / bat_cons["eval_matches"].clip(lower=1)) * 100.0
bat_elig = bat_elig.merge(bat_cons[["striker_id", "Consistency_Pct"]], on="striker_id", how="left")
bat_elig["Consistency_Pct"] = bat_elig["Consistency_Pct"].fillna(40.0)

# Empirical Bayes Shrinkage for RAA_100
mu_bat_raa = bat_elig["Raw_RAA_100"].mean()
K_bat = 40.0
bat_elig["shrink_w"] = bat_elig["hp_balls"] / (bat_elig["hp_balls"] + K_bat)
bat_elig["Pressure_RAA_100"] = bat_elig["shrink_w"] * bat_elig["Raw_RAA_100"] + (1 - bat_elig["shrink_w"]) * mu_bat_raa

# -------------------------------------------------------------
# 3 INDIVIDUAL BATTING MODELS
# -------------------------------------------------------------
# Model 1: Contextual Machine Learning Expectation Model (RAAE/100 + Wicket Preservation)
bat_elig["score_model_1"] = bat_elig["Pressure_RAA_100"] + 5.0 * bat_elig["Wicket_Preservation"]

# Model 2: Performance Elevation / Baseline Delta Model (Delta SR + Pressure SR)
bat_elig["score_model_2"] = bat_elig["Delta_SR"].fillna(0) + 0.3 * (bat_elig["Pressure_SR"] - 135.0)

# Model 3: Clutch Match Consistency & Reliability Model (Consistency % x log(HP balls))
bat_elig["score_model_3"] = bat_elig["Consistency_Pct"] * np.log10(bat_elig["hp_balls"].clip(lower=10))

# =============================================================================
# 4. BOWLING MODELS & ENSEMBLE
# =============================================================================
print("\n" + "=" * 70)
print("4. MODELING BOWLERS UNDER PRESSURE")
print("=" * 70)

bowl_legal = bbb[bbb["is_bowler_legal"] == 1].copy()
hp_mask_bowl = hp_mask.loc[bowl_legal.index]

hp_bowl = bowl_legal[hp_mask_bowl].groupby("bowler_id").agg(
    player_name=("bowler_name", "first"),
    hp_matches=("match_id", "nunique"),
    hp_balls=("is_bowler_legal", "sum"),
    hp_runs_conceded=("bowler_runs_conceded", "sum"),
    hp_xruns=("xRuns_bowl", "sum"),
    hp_wkts=("is_bowler_wkt", "sum"),
    hp_xwkt=("xWkt_bowl", "sum"),
    hp_dots=("bowler_runs_conceded", lambda s: (s == 0).sum()),
    hp_fours=("is_four", lambda s: (s == True).sum()),
    hp_sixes=("is_six", lambda s: (s == True).sum())
).reset_index()

us_bowl = bowl_legal[~hp_mask_bowl].groupby("bowler_id").agg(
    us_matches=("match_id", "nunique"),
    us_balls=("is_bowler_legal", "sum"),
    us_runs_conceded=("bowler_runs_conceded", "sum"),
    us_wkts=("is_bowler_wkt", "sum")
).reset_index()

bowl_df = hp_bowl.merge(us_bowl, on="bowler_id", how="left")
bowl_df["latest_match_date"] = bowl_df["bowler_id"].map(player_last_date)
bowl_df["player_name"] = bowl_df["bowler_id"].map(player_names).fillna(bowl_df["player_name"])

# Apply filters
bowl_elig = bowl_df[
    (bowl_df["hp_balls"] >= 120) &
    (bowl_df["bowler_id"].isin(active_players)) &
    (~bowl_df["bowler_id"].isin(pak_only_players)) &
    (~bowl_df["bowler_id"].isin(retired_pids)) &
    (~bowl_df["player_name"].isin(RETIRED_EXCLUSION_LIST))
].copy()

print(f"Qualified Bowlers meeting all filters (>=120 HP balls, active, non-Pak): {len(bowl_elig)}")

# Bowling core metrics
bowl_elig["Pressure_Econ"] = (bowl_elig["hp_runs_conceded"] / (bowl_elig["hp_balls"] / 6.0))
bowl_elig["Usual_Econ"] = np.where(bowl_elig["us_balls"] >= 24, (bowl_elig["us_runs_conceded"] / (bowl_elig["us_balls"] / 6.0)), np.nan)
bowl_elig["Delta_Econ"] = bowl_elig["Usual_Econ"] - bowl_elig["Pressure_Econ"]  # Positive means runs suppressed
bowl_elig["Raw_RSAE_24"] = ((bowl_elig["hp_xruns"] - bowl_elig["hp_runs_conceded"]) / bowl_elig["hp_balls"]) * 24.0
bowl_elig["Wickets_Above_Exp"] = bowl_elig["hp_wkts"] - bowl_elig["hp_xwkt"]

# Match-level consistency for bowlers
hp_match_bowl = bowl_legal[hp_mask_bowl].groupby(["bowler_id", "match_id"]).agg(
    m_balls=("is_bowler_legal", "sum"),
    m_runs=("bowler_runs_conceded", "sum"),
    m_xruns=("xRuns_bowl", "sum")
).reset_index()
hp_match_bowl = hp_match_bowl[hp_match_bowl["m_balls"] >= 6]
hp_match_bowl["pos_impact"] = hp_match_bowl["m_xruns"] > hp_match_bowl["m_runs"]

bowl_cons = hp_match_bowl.groupby("bowler_id").agg(
    eval_matches=("pos_impact", "count"),
    pos_matches=("pos_impact", "sum")
).reset_index()
bowl_cons["Consistency_Pct"] = (bowl_cons["pos_matches"] / bowl_cons["eval_matches"].clip(lower=1)) * 100.0
bowl_elig = bowl_elig.merge(bowl_cons[["bowler_id", "Consistency_Pct"]], on="bowler_id", how="left")
bowl_elig["Consistency_Pct"] = bowl_elig["Consistency_Pct"].fillna(40.0)

# Empirical Bayes Shrinkage for RSAE_24
mu_bowl_rsae = bowl_elig["Raw_RSAE_24"].mean()
K_bowl = 40.0
bowl_elig["shrink_w"] = bowl_elig["hp_balls"] / (bowl_elig["hp_balls"] + K_bowl)
bowl_elig["Pressure_RSAE_24"] = bowl_elig["shrink_w"] * bowl_elig["Raw_RSAE_24"] + (1 - bowl_elig["shrink_w"]) * mu_bowl_rsae

# -------------------------------------------------------------
# 3 INDIVIDUAL BOWLING MODELS
# -------------------------------------------------------------
# Model 1: Contextual Expectation & Runs Saved Model (RSAE/24 + Wickets Above Expected)
bowl_elig["score_model_1"] = bowl_elig["Pressure_RSAE_24"] + 0.5 * bowl_elig["Wickets_Above_Exp"]

# Model 2: Performance Elevation / Economy Suppression Model (Delta Econ & Pressure Economy)
bowl_elig["score_model_2"] = bowl_elig["Delta_Econ"].fillna(0) + 0.3 * (8.5 - bowl_elig["Pressure_Econ"])

# Model 3: Clutch Match Consistency & Reliability Model (Consistency % x log(HP balls))
bowl_elig["score_model_3"] = bowl_elig["Consistency_Pct"] * np.log10(bowl_elig["hp_balls"].clip(lower=10))

# =============================================================================
# 5. STANDARDIZATION & ENSEMBLE COMBINATION
# =============================================================================
def compute_ensemble_ratings(df, id_col):
    res = df.copy()
    # 1. Standardize Z-scores
    for i in [1, 2, 3]:
        res[f"z_score_m{i}"] = zscore(res[f"score_model_{i}"]).round(4)
        res[f"rank_m{i}"] = res[f"score_model_{i}"].rank(ascending=False, method="min").astype(int)
    
    # 2. Weighted Z-Score Ensemble (Weights: M1=0.40, M2=0.35, M3=0.25)
    w1, w2, w3 = 0.40, 0.35, 0.25
    res["weighted_z_score"] = (w1 * res["z_score_m1"] + w2 * res["z_score_m2"] + w3 * res["z_score_m3"]).round(4)
    
    # Equal-weight Z-score ensemble
    res["equal_weight_z_score"] = ((res["z_score_m1"] + res["z_score_m2"] + res["z_score_m3"]) / 3.0).round(4)
    
    # 3. Reciprocal Rank Fusion (RRF): sum(1 / (10 + rank))
    res["rrf_score"] = (
        (1.0 / (10.0 + res["rank_m1"])) +
        (1.0 / (10.0 + res["rank_m2"])) +
        (1.0 / (10.0 + res["rank_m3"]))
    ).round(4)
    
    # 4. Final Ensemble Score (rescaled to [0, 100])
    z_min, z_max = res["weighted_z_score"].min(), res["weighted_z_score"].max()
    res["final_ensemble_score"] = (((res["weighted_z_score"] - z_min) / (z_max - z_min)) * 100.0).round(2)
    
    # Sort and rank
    res = res.sort_values("final_ensemble_score", ascending=False).reset_index(drop=True)
    res["final_rank"] = range(1, len(res) + 1)
    
    # Map teams
    res["ipl_teams"] = res[id_col].map(lambda pid: ", ".join(player_ipl_teams.get(pid, ["None"])))
    res["all_teams"] = res[id_col].map(lambda pid: ", ".join(player_all_teams.get(pid, ["Unknown"])))
    
    # Spearman Correlation Matrix
    corr_cols = ["score_model_1", "score_model_2", "score_model_3", "equal_weight_z_score", "weighted_z_score", "rrf_score"]
    corr_matrix = res[corr_cols].corr(method="spearman").round(4)
    
    return res, corr_matrix

bat_ensemble, bat_corr = compute_ensemble_ratings(bat_elig, "striker_id")
bowl_ensemble, bowl_corr = compute_ensemble_ratings(bowl_elig, "bowler_id")

# Save outputs
for d in OUT_DIRS:
    bat_ensemble.head(15).to_csv(f"{d}/top15_ensemble_batters.csv", index=False)
    bowl_ensemble.head(15).to_csv(f"{d}/top15_ensemble_bowlers.csv", index=False)
    bat_corr.to_csv(f"{d}/ensemble_correlation_matrix_batters.csv")
    bowl_corr.to_csv(f"{d}/ensemble_correlation_matrix_bowlers.csv")
    bat_ensemble.to_csv(f"{d}/full_eligible_pool_batters.csv", index=False)
    bowl_ensemble.to_csv(f"{d}/full_eligible_pool_bowlers.csv", index=False)

print("\n" + "=" * 70)
print("BATTER ENSEMBLE SPEARMAN CORRELATION MATRIX")
print("=" * 70)
print(bat_corr)

print("\n" + "=" * 70)
print("BOWLER ENSEMBLE SPEARMAN CORRELATION MATRIX")
print("=" * 70)
print(bowl_corr)

# Print Top 15 Tables
print("\n" + "=" * 70)
print("FINAL TOP 15 BATTERS UNDER PRESSURE")
print("=" * 70)
bat_cols_display = [
    "final_rank", "striker_id", "player_name", "latest_match_date", "hp_balls",
    "rank_m1", "rank_m2", "rank_m3", "z_score_m1", "z_score_m2", "z_score_m3",
    "weighted_z_score", "rrf_score", "final_ensemble_score", "ipl_teams"
]
print(bat_ensemble[bat_cols_display].head(15).to_string(index=False))

print("\n" + "=" * 70)
print("FINAL TOP 15 BOWLERS UNDER PRESSURE")
print("=" * 70)
bowl_cols_display = [
    "final_rank", "bowler_id", "player_name", "latest_match_date", "hp_balls",
    "rank_m1", "rank_m2", "rank_m3", "z_score_m1", "z_score_m2", "z_score_m3",
    "weighted_z_score", "rrf_score", "final_ensemble_score", "ipl_teams"
]
print(bowl_ensemble[bowl_cols_display].head(15).to_string(index=False))

print("\nProcessing complete! All tables and correlation matrices saved successfully.")

