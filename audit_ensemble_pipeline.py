"""
audit_ensemble_pipeline.py
==========================
Comprehensive Ensemble Diagnostic Audit & Robustness Verification Script
for Rajasthan Royals SupeRR Selector Season 2 (Round 1).

Executes:
  1. Merge & Null Integrity Check (strict player_id joins, 0 nulls, active & nationality filter confirmation).
  2. Z-Score Standardization Audit (mean ~ 0.00, std ~ 1.00, Euler portfolio variance decomposition).
  3. Consensus & Stability Metrics (Spearman rank correlation, consensus centroid proof, Top 15 spread tables, outlier flagging).
  4. Weight Perturbation & Sensitivity Check (Equal-weight, RRF, +/-10% weight shifts, Top-10 overlap %, Spearman rho).
"""

import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, zscore

DATA_DIR = "./data"
if not os.path.exists(DATA_DIR):
    DATA_DIR = "6af3166e7b922_data_pack"

OUTPUT_DIR = "./outputs"

def print_header(title):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def print_section(title):
    print("\n" + "-" * 80)
    print(f" >> {title}")
    print("-" * 80)

# Load data
bat_df = pd.read_csv(f"{OUTPUT_DIR}/full_eligible_pool_batters.csv")
bowl_df = pd.read_csv(f"{OUTPUT_DIR}/full_eligible_pool_bowlers.csv")
teams = pd.read_csv(f"{DATA_DIR}/teams.csv")
comps = pd.read_csv(f"{DATA_DIR}/competitions.csv")
cmap = pd.read_csv(f"{DATA_DIR}/competition_team_player_mapping.csv")

audit_results = []

# =============================================================================
# 1. MERGE & NULL INTEGRITY CHECK
# =============================================================================
print_header("1. Merge & Null Integrity Check")

# 1.1 Key Join Type Verification
bat_key = "striker_id"
bowl_key = "bowler_id"
bat_key_is_int = np.issubdtype(bat_df[bat_key].dtype, np.integer)
bowl_key_is_int = np.issubdtype(bowl_df[bowl_key].dtype, np.integer)

print(f"[*] Batters primary key: '{bat_key}' (Integer type: {bat_key_is_int})")
print(f"[*] Bowlers primary key: '{bowl_key}' (Integer type: {bowl_key_is_int})")

p1_key_check = bat_key_is_int and bowl_key_is_int and bat_key in bat_df.columns and bowl_key in bowl_df.columns
audit_results.append(("Key Join Integrity (Merged on player_id, not name)", "PASS" if p1_key_check else "FAIL"))

# 1.2 Eligible Player Counts & Null Audit
score_cols = ["score_model_1", "score_model_2", "score_model_3", "z_score_m1", "z_score_m2", "z_score_m3", "weighted_z_score", "rrf_score"]

bat_nulls = bat_df[score_cols].isna().sum().sum()
bowl_nulls = bowl_df[score_cols].isna().sum().sum()

print(f"\n[*] Batters Pool Size: {len(bat_df)} qualified players")
print(f"    - Model 1 Valid Scores: {bat_df['score_model_1'].notna().sum()} / {len(bat_df)}")
print(f"    - Model 2 Valid Scores: {bat_df['score_model_2'].notna().sum()} / {len(bat_df)}")
print(f"    - Model 3 Valid Scores: {bat_df['score_model_3'].notna().sum()} / {len(bat_df)}")
print(f"    - Total Missing/NaN Values Across All Score Columns: {bat_nulls}")

print(f"\n[*] Bowlers Pool Size: {len(bowl_df)} qualified players")
print(f"    - Model 1 Valid Scores: {bowl_df['score_model_1'].notna().sum()} / {len(bowl_df)}")
print(f"    - Model 2 Valid Scores: {bowl_df['score_model_2'].notna().sum()} / {len(bowl_df)}")
print(f"    - Model 3 Valid Scores: {bowl_df['score_model_3'].notna().sum()} / {len(bowl_df)}")
print(f"    - Total Missing/NaN Values Across All Score Columns: {bowl_nulls}")

p1_null_check = (bat_nulls == 0) and (bowl_nulls == 0)
audit_results.append(("Null / NaN Integrity (0 missing values across all models)", "PASS" if p1_null_check else "FAIL"))

# 1.3 Excluded Players Audit
ipl_comps = set(comps[comps["comp_name"].str.contains("IPL", case=False, na=False)]["comp_id"].unique())
cmap_ipl = cmap[cmap["comp_id"].isin(ipl_comps)]
ipl_pids = set(cmap_ipl["player_id"].unique())

pak_teams = set(teams[teams["team_name"].str.contains("Pakistan", case=False, na=False)]["team_id"].unique())
pak_pids = set(cmap[cmap["team_id"].isin(pak_teams)]["player_id"].unique())
pak_only_pids = pak_pids - ipl_pids

bat_pak = set(bat_df[bat_key]) & pak_only_pids
bowl_pak = set(bowl_df[bowl_key]) & pak_only_pids

print(f"\n[*] Pakistan-Only Players Filter:")
print(f"    - Total Pakistan-only players identified: {len(pak_only_pids)}")
print(f"    - Present in Batters Pool: {len(bat_pak)}")
print(f"    - Present in Bowlers Pool: {len(bowl_pak)}")

# Inactive pre-2025 players
bat_inactive = (bat_df["latest_match_date"] < "2025-01-01").sum()
bowl_inactive = (bowl_df["latest_match_date"] < "2025-01-01").sum()

print(f"\n[*] Active Recency Filter (latest_match_date >= 2025-01-01):")
print(f"    - Inactive pre-2025 in Batters Pool: {bat_inactive}")
print(f"    - Inactive pre-2025 in Bowlers Pool: {bowl_inactive}")

# Manual Retired Exclusion List
RETIRED_EXCLUSIONS = [
    "Dinesh Karthik", "Shikhar Dhawan", "Kieron Pollard",
    "Ambati Rayudu", "Suresh Raina", "Vijay Shankar", "Moeen Ali"
]
bat_retired = bat_df[bat_df["player_name"].isin(RETIRED_EXCLUSIONS)]["player_name"].tolist()
bowl_retired = bowl_df[bowl_df["player_name"].isin(RETIRED_EXCLUSIONS)]["player_name"].tolist()

print(f"\n[*] Retired / Withdrawn Manual Exclusions:")
print(f"    - Excluded list: {RETIRED_EXCLUSIONS}")
print(f"    - Present in Batters Pool: {bat_retired}")
print(f"    - Present in Bowlers Pool: {bowl_retired}")

p1_exclusion_check = (len(bat_pak) == 0 and len(bowl_pak) == 0 and
                      bat_inactive == 0 and bowl_inactive == 0 and
                      len(bat_retired) == 0 and len(bowl_retired) == 0)
audit_results.append(("Eligibility & Active Screening (Pak-only, inactive, retired excluded)", "PASS" if p1_exclusion_check else "FAIL"))


# =============================================================================
# 2. Z-SCORE STANDARDIZATION AUDIT
# =============================================================================
print_header("2. Z-Score Standardization & Variance Contribution Audit")

def audit_zscores(df, role_name):
    print(f"\n[*] {role_name} Standardization Metrics (N = {len(df)}):")
    print(f"    {'Model':<25} | {'Mean':>10} | {'Std Dev':>10} | {'Status':>8}")
    print("    " + "-" * 60)
    all_ok = True
    for i in [1, 2, 3]:
        col = f"z_score_m{i}"
        m = df[col].mean()
        s = df[col].std(ddof=0)
        ok = abs(m) < 1e-4 and abs(s - 1.0) < 1e-4
        if not ok:
            all_ok = False
        print(f"    {col:<25} | {m:>10.6f} | {s:>10.6f} | {'[PASS]' if ok else '[FAIL]':>8}")
    return all_ok

bat_z_ok = audit_zscores(bat_df, "Batters")
bowl_z_ok = audit_zscores(bowl_df, "Bowlers")
audit_results.append(("Z-Score Calibration (Mean = 0.00, Std = 1.00 for all models)", "PASS" if (bat_z_ok and bowl_z_ok) else "FAIL"))

# Euler Variance Decomposition: Var(w^T Z) = sum(w_i * (Cov @ w)_i)
def compute_variance_contribution(df, w=np.array([0.40, 0.35, 0.25])):
    Z = df[["z_score_m1", "z_score_m2", "z_score_m3"]].values
    cov = np.cov(Z, rowvar=False)
    total_var = float(w.T @ cov @ w)
    marginal_contrib = (w * (cov @ w)) / total_var * 100.0
    return cov, total_var, marginal_contrib

w_nominal = np.array([0.40, 0.35, 0.25])
cov_bat, var_bat, vc_bat = compute_variance_contribution(bat_df, w_nominal)
cov_bowl, var_bowl, vc_bowl = compute_variance_contribution(bowl_df, w_nominal)

print("\n[*] Effective Variance Contribution to Ensemble Score (Euler Decomposition):")
print(f"    {'Model Paradigm':<32} | {'Nominal Weight':>14} | {'Batters Var %':>13} | {'Bowlers Var %':>13}")
print("    " + "-" * 78)
model_names = [
    "Model 1 (Contextual ML Expectation)",
    "Model 2 (Rate Elevation Delta)",
    "Model 3 (Clutch Match Consistency)"
]
for i in range(3):
    print(f"    {model_names[i]:<32} | {w_nominal[i]*100:>13.1f}% | {vc_bat[i]:>12.2f}% | {vc_bowl[i]:>12.2f}%")
print(f"    {'Total Portfolio Variance':<32} | {'100.0%':>14} | {np.sum(vc_bat):>12.2f}% | {np.sum(vc_bowl):>12.2f}%")

# Check dominance (no model should contribute > 55% of total variance)
max_vc = max(np.max(vc_bat), np.max(vc_bowl))
no_dominance = max_vc < 55.0
print(f"\n[*] Maximum single-model variance contribution: {max_vc:.2f}% (Threshold < 55.0%)")
audit_results.append(("Variance Attribution (No single model silently dominates)", "PASS" if no_dominance else "FAIL"))


# =============================================================================
# 3. CONSENSUS & STABILITY METRICS (FOR METHODOLOGY REPORT)
# =============================================================================
print_header("3. Consensus & Stability Metrics")

def print_correlation_analysis(df, role_name):
    print_section(f"{role_name} Spearman Rank Correlation & Consensus Centroid Analysis")
    cols = ["score_model_1", "score_model_2", "score_model_3", "weighted_z_score"]
    col_labels = ["M1 (Context)", "M2 (Delta)", "M3 (Consistency)", "Ensemble (Weighted Z)"]
    
    corr_df = df[cols].corr(method="spearman")
    corr_display = corr_df.copy()
    corr_display.columns = col_labels
    corr_display.index = col_labels
    print(corr_display.round(4).to_string())
    
    # Compute mean correlation of each model with other base models
    base_cols = ["score_model_1", "score_model_2", "score_model_3"]
    mean_corrs = {}
    for c in cols:
        others = [b for b in base_cols if b != c]
        mean_corrs[c] = corr_df.loc[c, others].mean()
    
    print(f"\n[*] Mean Correlation with Base Models:")
    for c, lbl in zip(cols, col_labels):
        print(f"    - {lbl:<25}: {mean_corrs[c]:.4f}")
    
    ensemble_is_highest = mean_corrs["weighted_z_score"] > max(mean_corrs["score_model_1"], mean_corrs["score_model_2"], mean_corrs["score_model_3"])
    print(f"    - Consensus Centroid Validation: {'[PASS] Ensemble achieves HIGHEST mean correlation' if ensemble_is_highest else '[FAIL]'}")
    return ensemble_is_highest

bat_centroid_ok = print_correlation_analysis(bat_df, "Batters")
bowl_centroid_ok = print_correlation_analysis(bowl_df, "Bowlers")
audit_results.append(("Consensus Centroid Concordance (Ensemble has highest mean correlation)", "PASS" if (bat_centroid_ok and bowl_centroid_ok) else "FAIL"))

# Top 15 Comparison Tables & Spread Flagging
def build_top15_table(df, id_col, role_name):
    print_section(f"Final Top 15 {role_name} Model Ranks & Spread Inspection")
    res = df.sort_values("final_rank").head(15).copy()
    res["rrf_rank"] = res["rrf_score"].rank(ascending=False, method="min").astype(int)
    res["max_rank_spread"] = res[["rank_m1", "rank_m2", "rank_m3"]].max(axis=1) - res[["rank_m1", "rank_m2", "rank_m3"]].min(axis=1)
    
    # Print formatted table
    print(f"{'Rank':<4} | {'ID':<6} | {'Player Name':<20} | {'HP Balls':>8} | {'M1':>3} | {'M2':>3} | {'M3':>3} | {'Spread':>6} | {'Score':>7} | {'RRF':>4} | {'Flag'}")
    print("-" * 92)
    
    flagged_top10 = []
    for _, r in res.iterrows():
        rank = int(r["final_rank"])
        pid = int(r[id_col])
        name = str(r["player_name"])[:20]
        hp = int(r["hp_balls"])
        m1 = int(r["rank_m1"])
        m2 = int(r["rank_m2"])
        m3 = int(r["rank_m3"])
        spread = int(r["max_rank_spread"])
        score = float(r["final_ensemble_score"])
        rrf = int(r["rrf_rank"])
        
        flag = ""
        if rank <= 10 and spread > 8:
            flag = "FLAG (Spread > 8)"
            flagged_top10.append((rank, name, spread, m1, m2, m3))
        elif rank <= 10:
            flag = "OK"
        else:
            flag = "Backup"
            
        print(f"{rank:<4} | {pid:<6} | {name:<20} | {hp:>8} | {m1:>3} | {m2:>3} | {m3:>3} | {spread:>6} | {score:>7.2f} | {rrf:>4} | {flag}")
    
    print(f"\n[*] Top 10 Players with Max Rank Spread > 8 spots: {len(flagged_top10)}")
    for f in flagged_top10:
        print(f"    - Rank {f[0]} {f[1]}: Spread = {f[2]} (M1: #{f[3]}, M2: #{f[4]}, M3: #{f[5]})")
    return flagged_top10

bat_flagged = build_top15_table(bat_df, "striker_id", "Batters")
bowl_flagged = build_top15_table(bowl_df, "bowler_id", "Bowlers")


# =============================================================================
# 4. WEIGHT PERTURBATION & SENSITIVITY CHECK
# =============================================================================
print_header("4. Weight Perturbation & Sensitivity Check")

perturbations = [
    ("Baseline (40/35/25)", np.array([0.40, 0.35, 0.25])),
    ("Equal Weights (33/33/33)", np.array([1/3, 1/3, 1/3])),
    ("Perturbation +10% M1 (44/33/23)", np.array([0.44, 0.33, 0.23])),
    ("Perturbation +10% M2 (36/42/22)", np.array([0.36, 0.42, 0.22])),
    ("Perturbation +10% M3 (36/31/33)", np.array([0.36, 0.31, 0.33])),
    ("Perturbation -10% M1 (36/37/27)", np.array([0.36, 0.37, 0.27])),
    ("Perturbation -10% M2 (43/31/26)", np.array([0.43, 0.31, 0.26])),
]

def run_sensitivity_audit(df, id_col, role_name):
    print_section(f"{role_name} Sensitivity & Stability Audit (N = {len(df)})")
    
    base_scores = 0.40 * df["z_score_m1"] + 0.35 * df["z_score_m2"] + 0.25 * df["z_score_m3"]
    base_top10 = set(df.assign(score=base_scores).sort_values("score", ascending=False).head(10)[id_col])
    
    print(f"{'Variant / Perturbation Scheme':<36} | {'Weights (M1/M2/M3)':<20} | {'Top-10 Overlap':>14} | {'Spearman Rho':>12}")
    print("-" * 88)
    
    all_rhos_high = True
    for name, w in perturbations:
        scores = w[0] * df["z_score_m1"] + w[1] * df["z_score_m2"] + w[2] * df["z_score_m3"]
        v_top10 = set(df.assign(score=scores).sort_values("score", ascending=False).head(10)[id_col])
        overlap_pct = (len(base_top10 & v_top10) / 10.0) * 100.0
        rho, _ = spearmanr(base_scores, scores)
        w_str = f"{w[0]:.2f} / {w[1]:.2f} / {w[2]:.2f}"
        if rho < 0.95:
            all_rhos_high = False
        print(f"{name:<36} | {w_str:<20} | {overlap_pct:>13.1f}% | {rho:>12.4f}")
    
    # Also evaluate Reciprocal Rank Fusion (RRF)
    rrf_top10 = set(df.sort_values("rrf_score", ascending=False).head(10)[id_col])
    rrf_overlap = (len(base_top10 & rrf_top10) / 10.0) * 100.0
    rho_rrf, _ = spearmanr(base_scores, df["rrf_score"])
    print(f"{'Reciprocal Rank Fusion (RRF)':<36} | {'Rank Inversion':<20} | {rrf_overlap:>13.1f}% | {rho_rrf:>12.4f}")
    
    return all_rhos_high, rho_rrf

bat_sens_ok, bat_rrf_rho = run_sensitivity_audit(bat_df, "striker_id", "Batters")
bowl_sens_ok, bowl_rrf_rho = run_sensitivity_audit(bowl_df, "bowler_id", "Bowlers")

audit_results.append(("Weight Perturbation Stability (Spearman rho >= 0.95 across +/-10% shifts)", "PASS" if (bat_sens_ok and bowl_sens_ok) else "FAIL"))
audit_results.append(("RRF Rank Fusion Concordance (Spearman rho >= 0.95 with baseline ensemble)", "PASS" if (bat_rrf_rho >= 0.95 and bowl_rrf_rho >= 0.95) else "FAIL"))


# =============================================================================
# 5. OVERALL VERIFICATION SUMMARY
# =============================================================================
print_header("5. Ensemble Audit Verification Summary")
print(f"{'Check / Verification Item':<65} | {'Verdict':>8}")
print("-" * 76)
all_pass = True
for item, status in audit_results:
    if status != "PASS":
        all_pass = False
    print(f"{item:<65} | {status:>8}")
print("-" * 76)
print(f"{'OVERALL PIPELINE DIAGNOSTIC STATUS':<65} | {'[ALL PASS]' if all_pass else '[FAIL]':>8}")
print("=" * 80)

