"""
Script to test the 3 models and ensemble aggregation
"""
import pandas as pd
import numpy as np
from scipy.stats import spearmanr, zscore

DATA_DIR = "6af3166e7b922_data_pack"
mat = pd.read_csv(f"{DATA_DIR}/matches.csv", low_memory=False)
teams = pd.read_csv(f"{DATA_DIR}/teams.csv", low_memory=False)
comps = pd.read_csv(f"{DATA_DIR}/competitions.csv", low_memory=False)
cmap = pd.read_csv(f"{DATA_DIR}/competition_team_player_mapping.csv", low_memory=False)
bbb = pd.read_csv(f"{DATA_DIR}/ball_by_ball.csv", low_memory=False)
pi_df = pd.read_feather("temp_bbb_pi.feather")

# Add features to bbb
bbb["PI"] = pi_df["PI"]
bbb["xRuns_bat"] = pi_df["xRuns_bat"]
bbb["xRuns_bowl"] = pi_df["xRuns_bowl"]
bbb["xWkt_bat"] = pi_df["xWkt_bat"]
bbb["xWkt_bowl"] = pi_df["xWkt_bowl"]

# Match dates
m_dates = mat.set_index("match_id")["match_date"].to_dict()
bbb["match_date"] = bbb["match_id"].map(m_dates)

# Legal flags
bbb["is_batter_legal"] = (bbb["extras_type"] != "wide").astype(int)
bbb["is_bowler_legal"] = (~bbb["extras_type"].isin(["wide", "Overstep"])).astype(int)

# Bowler runs conceded = bat runs + wide + noball + extras_2_runs
wide_noball = bbb["extras_type"].isin(["wide", "Overstep"]).astype(int)
bbb["bowler_runs_conceded"] = bbb["runs"].fillna(0) + wide_noball + bbb["extras_2_runs"].fillna(0)

bowler_wkt_kinds = ["Bowled", "Caught", "LBW", "Stump", "Hit Wicket"]
bbb["is_bowler_wkt"] = (bbb["is_wicket"] == True) & (bbb["dismissal_type"].isin(bowler_wkt_kinds))
bbb["is_bowler_wkt"] = bbb["is_bowler_wkt"].astype(int)

striker_out = (bbb["is_wicket"] == True) & (
    (bbb["dismissal_type"] != "RunOut") | (bbb["dismissed_player_id"] == bbb["striker_id"])
)
bbb["is_striker_out"] = striker_out.astype(int)

# 1. FILTERS
# Pakistan-only exclusion
pak_teams = teams[teams["team_name"].str.contains("Pakistan", case=False, na=False)]["team_id"].unique()
ipl_comps = comps[comps["comp_name"].str.contains("IPL", case=False, na=False)]["comp_id"].unique()
pak_players = set(cmap[cmap["team_id"].isin(pak_teams)]["player_id"].unique())
ipl_players = set(cmap[cmap["comp_id"].isin(ipl_comps)]["player_id"].unique())
pak_only_players = pak_players - ipl_players

# Active cutoff >= 2025-01-01
striker_dates = bbb.groupby("striker_id")["match_date"].max()
bowler_dates = bbb.groupby("bowler_id")["match_date"].max()
player_last_date = pd.concat([striker_dates, bowler_dates]).groupby(level=0).max().to_dict()
active_players = {pid for pid, d in player_last_date.items() if str(d) >= "2025-01-01"}

# Configurable retired exclusion list
RETIRED_EXCLUSION_LIST = [
    # Players retired in 2024/2025/2026 or confirmed unavailable in Unstop
    # e.g., Dinesh Karthik (retired 2024), Shikhar Dhawan (retired 2024)
    "Dinesh Karthik",
    "Shikhar Dhawan",
    "Kieron Pollard",
    "Ambati Rayudu",
    "Suresh Raina",
]
retired_pids = set(cmap[cmap["player_name"].isin(RETIRED_EXCLUSION_LIST)]["player_id"].unique())

print(f"Pakistan-only excluded: {len(pak_only_players)}")
print(f"Active players: {len(active_players)}")
print(f"Retired manual exclusions: {len(retired_pids)}")

# Pressure mask
hp_mask = bbb["PI"] >= 0.65

# -------------------------------------------------------------
# BATTING MODELS
# -------------------------------------------------------------
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

# Filter eligible pool
bat_elig = bat_df[
    (bat_df["hp_balls"] >= 120) &
    (bat_df["striker_id"].isin(active_players)) &
    (~bat_df["striker_id"].isin(pak_only_players)) &
    (~bat_df["striker_id"].isin(retired_pids)) &
    (~bat_df["player_name"].isin(RETIRED_EXCLUSION_LIST))
].copy()

print(f"Eligible qualified batters (>=120 HP balls): {len(bat_elig)}")

# Compute metrics for batters
bat_elig["Pressure_SR"] = (bat_elig["hp_runs"] / bat_elig["hp_balls"]) * 100.0
bat_elig["Usual_SR"] = np.where(bat_elig["us_balls"] >= 20, (bat_elig["us_runs"] / bat_elig["us_balls"]) * 100.0, np.nan)
bat_elig["Delta_SR"] = bat_elig["Pressure_SR"] - bat_elig["Usual_SR"]
bat_elig["Raw_RAA_100"] = ((bat_elig["hp_runs"] - bat_elig["hp_xruns"]) / bat_elig["hp_balls"]) * 100.0
bat_elig["Wicket_Preservation"] = bat_elig["hp_xwkt"] / bat_elig["hp_outs"].clip(lower=1)

# Match-level consistency
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

# MODEL 1: Contextual Expectation & Value-Added Model (RAAE/100 + Wicket Preservation)
# Measures total context-adjusted runs generated above expectation
bat_elig["score_model_1"] = bat_elig["Pressure_RAA_100"] + 5.0 * bat_elig["Wicket_Preservation"]

# MODEL 2: Performance Elevation / Baseline Delta Model (Delta SR & Pressure SR)
# Measures how much the batter elevates over their normal standard
bat_elig["score_model_2"] = bat_elig["Delta_SR"].fillna(0) + 0.3 * (bat_elig["Pressure_SR"] - 135.0)

# MODEL 3: Clutch Match Consistency & Reliability Model (Consistency % & Sample Volume Reliability)
# Measures delivery under pressure on a match-by-match basis
bat_elig["score_model_3"] = bat_elig["Consistency_Pct"] * np.log10(bat_elig["hp_balls"].clip(lower=10))

print("Batting models computed successfully.")

# -------------------------------------------------------------
# BOWLING MODELS
# -------------------------------------------------------------
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

# Filter eligible pool
bowl_elig = bowl_df[
    (bowl_df["hp_balls"] >= 120) &
    (bowl_df["bowler_id"].isin(active_players)) &
    (~bowl_df["bowler_id"].isin(pak_only_players)) &
    (~bowl_df["bowler_id"].isin(retired_pids)) &
    (~bowl_df["player_name"].isin(RETIRED_EXCLUSION_LIST))
].copy()

print(f"Eligible qualified bowlers (>=120 HP balls): {len(bowl_elig)}")

# Compute metrics for bowlers
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

# MODEL 1: Contextual Expectation & Runs Saved Model (RSAE/24 + Wickets Above Expected)
bowl_elig["score_model_1"] = bowl_elig["Pressure_RSAE_24"] + 0.5 * bowl_elig["Wickets_Above_Exp"]

# MODEL 2: Performance Elevation / Economy Suppression Model (Delta Econ & Pressure Economy)
bowl_elig["score_model_2"] = bowl_elig["Delta_Econ"].fillna(0) + 0.3 * (8.5 - bowl_elig["Pressure_Econ"])

# MODEL 3: Clutch Match Consistency & Reliability Model (Consistency % & Sample Volume Reliability)
bowl_elig["score_model_3"] = bowl_elig["Consistency_Pct"] * np.log10(bowl_elig["hp_balls"].clip(lower=10))

print("Bowling models computed successfully.")

# -------------------------------------------------------------
# ENSEMBLE AGGREGATION & STANDARDIZATION
# -------------------------------------------------------------
def build_ensemble(df, id_col, is_bat=True):
    # 1. Z-scores
    for i in [1, 2, 3]:
        df[f"z_score_m{i}"] = zscore(df[f"score_model_{i}"])
        df[f"rank_m{i}"] = df[f"score_model_{i}"].rank(ascending=False, method="min").astype(int)
    
    # 2. Weighted Z-Score Ensemble (weights: M1: 0.40, M2: 0.35, M3: 0.25)
    # Rationale: M1 covers contextual expectation (40%), M2 covers player delta (35%), M3 covers consistency (25%)
    w1, w2, w3 = 0.40, 0.35, 0.25
    df["weighted_z_score"] = w1 * df["z_score_m1"] + w2 * df["z_score_m2"] + w3 * df["z_score_m3"]
    df["equal_weight_z_score"] = (df["z_score_m1"] + df["z_score_m2"] + df["z_score_m3"]) / 3.0
    
    # 3. Reciprocal Rank Fusion (RRF): sum(1 / (10 + rank))
    df["rrf_score"] = (1.0 / (10.0 + df["rank_m1"])) + (1.0 / (10.0 + df["rank_m2"])) + (1.0 / (10.0 + df["rank_m3"]))
    
    # Final Ensemble Score scaled 0 - 100
    # Rescale weighted_z_score to [0, 100] using standard sigmoid / min-max
    z_min, z_max = df["weighted_z_score"].min(), df["weighted_z_score"].max()
    df["final_ensemble_score"] = ((df["weighted_z_score"] - z_min) / (z_max - z_min) * 100.0).round(2)
    
    df = df.sort_values("final_ensemble_score", ascending=False).reset_index(drop=True)
    df["final_rank"] = range(1, len(df) + 1)
    
    # Spearman Correlation Matrix
    corr_cols = ["score_model_1", "score_model_2", "score_model_3", "equal_weight_z_score", "weighted_z_score", "rrf_score"]
    corr_matrix = df[corr_cols].corr(method="spearman").round(3)
    
    return df, corr_matrix

bat_final, bat_corr = build_ensemble(bat_elig, "striker_id", is_bat=True)
bowl_final, bowl_corr = build_ensemble(bowl_elig, "bowler_id", is_bat=False)

print("\n" + "=" * 60)
print("BATTER ENSEMBLE SPEARMAN CORRELATION MATRIX")
print("=" * 60)
print(bat_corr)

print("\n" + "=" * 60)
print("BOWLER ENSEMBLE SPEARMAN CORRELATION MATRIX")
print("=" * 60)
print(bowl_corr)

print("\n" + "=" * 60)
print("TOP 15 BATTERS UNDER PRESSURE (FINAL ENSEMBLE)")
print("=" * 60)
bat_show = bat_final[["final_rank", "striker_id", "player_name", "latest_match_date", "hp_balls", 
                      "rank_m1", "rank_m2", "rank_m3", "z_score_m1", "z_score_m2", "z_score_m3", 
                      "rrf_score", "final_ensemble_score"]].head(15)
print(bat_show.to_string(index=False))

print("\n" + "=" * 60)
print("TOP 15 BOWLERS UNDER PRESSURE (FINAL ENSEMBLE)")
print("=" * 60)
bowl_show = bowl_final[["final_rank", "bowler_id", "player_name", "latest_match_date", "hp_balls", 
                        "rank_m1", "rank_m2", "rank_m3", "z_score_m1", "z_score_m2", "z_score_m3", 
                        "rrf_score", "final_ensemble_score"]].head(15)
print(bowl_show.to_string(index=False))
