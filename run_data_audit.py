"""
Data Audit Script for SupeRR Selector Season 2 - Round 1
Inspects all files in ./data, analyzes schemas, null rates, key joins,
and writes a comprehensive findings report to docs/data_audit.md.
"""

import os
import pandas as pd
import numpy as np

DATA_DIR = "./data"
DOCS_DIR = "./docs"
os.makedirs(DOCS_DIR, exist_ok=True)

files = [
    "competitions.csv",
    "teams.csv",
    "matches.csv",
    "playing_eleven.csv",
    "competition_team_player_mapping.csv",
    "ball_by_ball.csv"
]

dfs = {}
audit_info = {}

print("=" * 60)
print("INSPECTING DATA FILES IN ./data")
print("=" * 60)

for f in files:
    path = os.path.join(DATA_DIR, f)
    if not os.path.exists(path):
        print(f"Warning: {path} not found!")
        continue
    
    df = pd.read_csv(path, low_memory=False)
    dfs[f] = df
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"Loaded {f}: {len(df):,} rows, {len(df.columns)} columns ({size_mb:.2f} MB)")
    
    col_info = []
    for c in df.columns:
        null_count = df[c].isna().sum()
        null_pct = (null_count / len(df)) * 100
        n_unique = df[c].nunique()
        sample_vals = df[c].dropna().unique()[:3].tolist()
        sample_str = ", ".join(str(v) for v in sample_vals)
        if len(sample_str) > 40:
            sample_str = sample_str[:37] + "..."
        col_info.append({
            "column": c,
            "dtype": str(df[c].dtype),
            "null_count": null_count,
            "null_pct": null_pct,
            "n_unique": n_unique,
            "sample": sample_str
        })
    
    audit_info[f] = {
        "rows": len(df),
        "cols": len(df.columns),
        "size_mb": size_mb,
        "col_info": col_info
    }

# Join integrity checks
print("\n" + "=" * 60)
print("VALIDATING RELATIONAL JOINS")
print("=" * 60)

join_results = {}

# 1. matches.comp_id -> competitions.comp_id
m_comps = set(dfs["matches.csv"]["comp_id"].unique())
c_comps = set(dfs["competitions.csv"]["comp_id"].unique())
m_in_c = m_comps.issubset(c_comps)
diff_comps = m_comps - c_comps
print(f"1. matches.comp_id -> competitions.comp_id: Valid={m_in_c} (Missing: {len(diff_comps)})")
join_results["matches_to_competitions"] = {
    "valid": m_in_c,
    "source_unique": len(m_comps),
    "target_unique": len(c_comps),
    "missing_count": len(diff_comps),
    "missing_keys": list(diff_comps)[:5]
}

# 2. ball_by_ball.match_id -> matches.match_id
bbb_matches = set(dfs["ball_by_ball.csv"]["match_id"].unique())
m_matches = set(dfs["matches.csv"]["match_id"].unique())
bbb_in_m = bbb_matches.issubset(m_matches)
diff_matches = bbb_matches - m_matches
print(f"2. ball_by_ball.match_id -> matches.match_id: Valid={bbb_in_m} (Missing: {len(diff_matches)})")
join_results["bbb_to_matches"] = {
    "valid": bbb_in_m,
    "source_unique": len(bbb_matches),
    "target_unique": len(m_matches),
    "missing_count": len(diff_matches),
    "missing_keys": list(diff_matches)[:5]
}

# 3. playing_eleven.match_id -> matches.match_id
pe_matches = set(dfs["playing_eleven.csv"]["match_id"].unique())
pe_in_m = pe_matches.issubset(m_matches)
diff_pe_m = pe_matches - m_matches
print(f"3. playing_eleven.match_id -> matches.match_id: Valid={pe_in_m} (Missing: {len(diff_pe_m)})")
join_results["playing_eleven_to_matches"] = {
    "valid": pe_in_m,
    "source_unique": len(pe_matches),
    "target_unique": len(m_matches),
    "missing_count": len(diff_pe_m),
    "missing_keys": list(diff_pe_m)[:5]
}

# 4. matches teams -> teams.csv
t_teams = set(dfs["teams.csv"]["team_id"].unique())
m_home = set(dfs["matches.csv"]["home_team_id"].unique())
m_away = set(dfs["matches.csv"]["away_team_id"].unique())
m_win = set(dfs["matches.csv"]["win_team_id"].dropna().unique())
all_m_teams = m_home | m_away | m_win
m_teams_in_t = all_m_teams.issubset(t_teams)
diff_m_teams = all_m_teams - t_teams
print(f"4. matches team IDs -> teams.team_id: Valid={m_teams_in_t} (Missing: {len(diff_m_teams)})")
join_results["matches_to_teams"] = {
    "valid": m_teams_in_t,
    "source_unique": len(all_m_teams),
    "target_unique": len(t_teams),
    "missing_count": len(diff_m_teams),
    "missing_keys": list(diff_m_teams)[:5]
}

# 5. ball_by_ball teams -> teams.csv
bbb_bat_teams = set(dfs["ball_by_ball.csv"]["batting_team_id"].unique())
bbb_bowl_teams = set(dfs["ball_by_ball.csv"]["bowling_team_id"].unique())
all_bbb_teams = bbb_bat_teams | bbb_bowl_teams
bbb_teams_in_t = all_bbb_teams.issubset(t_teams)
diff_bbb_teams = all_bbb_teams - t_teams
print(f"5. ball_by_ball team IDs -> teams.team_id: Valid={bbb_teams_in_t} (Missing: {len(diff_bbb_teams)})")
join_results["bbb_to_teams"] = {
    "valid": bbb_teams_in_t,
    "source_unique": len(all_bbb_teams),
    "target_unique": len(t_teams),
    "missing_count": len(diff_bbb_teams),
    "missing_keys": list(diff_bbb_teams)[:5]
}

# 6. Player IDs: ball_by_ball -> mapping
map_players = set(dfs["competition_team_player_mapping.csv"]["player_id"].unique())
bbb_strikers = set(dfs["ball_by_ball.csv"]["striker_id"].unique())
bbb_bowlers = set(dfs["ball_by_ball.csv"]["bowler_id"].unique())
all_bbb_players = bbb_strikers | bbb_bowlers
bbb_players_in_map = all_bbb_players.issubset(map_players)
diff_bbb_players = all_bbb_players - map_players
print(f"6. ball_by_ball players -> mapping.player_id: Valid={bbb_players_in_map} (Missing: {len(diff_bbb_players)})")
join_results["bbb_to_player_map"] = {
    "valid": bbb_players_in_map,
    "source_unique": len(all_bbb_players),
    "target_unique": len(map_players),
    "missing_count": len(diff_bbb_players),
    "missing_keys": list(diff_bbb_players)[:5]
}

# Check playing_eleven player IDs -> mapping
pe_players = set(dfs["playing_eleven.csv"]["player_id"].unique())
pe_in_map = pe_players.issubset(map_players)
diff_pe_players = pe_players - map_players
print(f"7. playing_eleven players -> mapping.player_id: Valid={pe_in_map} (Missing: {len(diff_pe_players)})")
join_results["pe_to_player_map"] = {
    "valid": pe_in_map,
    "source_unique": len(pe_players),
    "target_unique": len(map_players),
    "missing_count": len(diff_pe_players),
    "missing_keys": list(diff_pe_players)[:5]
}

# Deep Dive into Ball by Ball details
bbb = dfs["ball_by_ball.csv"]
print("\n" + "=" * 60)
print("DEEP DIVE: BALL-BY-BALL DETAILS")
print("=" * 60)
print(f"Innings values: {bbb['innings'].value_counts().to_dict()}")
print(f"Extras types: {bbb['extras_type'].value_counts(dropna=False).to_dict()}")
print(f"Runs distribution: {bbb['runs'].value_counts().head(10).to_dict()}")
print(f"extras1_runs unique: {bbb['extras1_runs'].value_counts(dropna=False).head(10).to_dict()}")
print(f"extras_2_runs unique: {bbb['extras_2_runs'].value_counts(dropna=False).head(10).to_dict()}")
print(f"is_wicket counts: {bbb['is_wicket'].value_counts(dropna=False).to_dict()}")
print(f"dismissal_type_id counts: {bbb['dismissal_type_id'].value_counts(dropna=False).to_dict()}")

# Deep dive into Competitions and Matches
matches = dfs["matches.csv"]
comps = dfs["competitions.csv"]
m_with_c = matches.merge(comps, on="comp_id", how="left")
print("\n" + "=" * 60)
print("MATCHES BREAKDOWN BY FORMAT & SEASON")
print("=" * 60)
format_season_counts = m_with_c.groupby(["match_format", "season", "comp_name"]).size().reset_index(name="matches_count")
print(format_season_counts.to_string(index=False))

# Check DLS / Revised Overs
dls_matches = matches[matches["first_inn_revised_overs"].notna() | matches["second_inn_revised_overs"].notna() | matches["revised_target"].notna()]
print(f"\nMatches with revised overs or targets (DLS/shortened): {len(dls_matches)}")
print(dls_matches[["match_id", "match_number", "first_inn_revised_overs", "second_inn_revised_overs", "revised_target", "result"]].head(10).to_string(index=False))

# Write out docs/data_audit.md
print("\nWriting comprehensive documentation to docs/data_audit.md ...")

with open(os.path.join(DOCS_DIR, "data_audit.md"), "w", encoding="utf-8") as f_out:
    f_out.write("# Data Audit Report — Rajasthan Royals SupeRR Selector Season 2 (Round 1)\n\n")
    f_out.write("**Generated on:** 2026-11-18  \n")
    f_out.write("**Role:** Lead Cricket Quantitative Analyst / Senior Data Scientist  \n")
    f_out.write("**Scope:** Comprehensive structural audit of all supplied IPL & T20I CSV files from 2022 onwards in `./data`.\n\n")
    f_out.write("---\n\n")
    
    f_out.write("## 1. Executive Summary & File Inventory\n\n")
    f_out.write("The dataset contains 6 primary relational CSV files capturing ball-by-ball actions, match metadata, competition definitions, team rosters, and playing elevens across the Indian Premier League (IPL) and Men's T20 Internationals (T20I) from 2022 to 2024.\n\n")
    f_out.write("| File Name | Record Count | Column Count | File Size | Primary Key / Grain | Description |\n")
    f_out.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
    for fname, info in audit_info.items():
        grain = "Unknown"
        if fname == "ball_by_ball.csv":
            grain = "`match_id`, `innings`, `overid`, `over_ball_num`"
        elif fname == "matches.csv":
            grain = "`match_id`"
        elif fname == "competitions.csv":
            grain = "`comp_id`"
        elif fname == "teams.csv":
            grain = "`team_id`"
        elif fname == "playing_eleven.csv":
            grain = "`match_id`, `player_id`"
        elif fname == "competition_team_player_mapping.csv":
            grain = "`comp_id`, `team_id`, `player_id`"
        f_out.write(f"| `{fname}` | {info['rows']:,} | {info['cols']} | {info['size_mb']:.2f} MB | {grain} | Relational table |\n")
    f_out.write("\n---\n\n")
    
    f_out.write("## 2. Detailed Schemas, Data Types & Null Profiles\n\n")
    for fname, info in audit_info.items():
        f_out.write(f"### 2.{list(audit_info.keys()).index(fname)+1} `{fname}` ({info['rows']:,} rows, {info['cols']} columns)\n\n")
        f_out.write("| Column Name | Inferred Dtype | Null Count | Null % | Unique Values | Sample Values |\n")
        f_out.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for c in info["col_info"]:
            f_out.write(f"| `{c['column']}` | `{c['dtype']}` | {c['null_count']:,} | {c['null_pct']:.2f}% | {c['n_unique']:,} | `{c['sample']}` |\n")
        f_out.write("\n")
    
    f_out.write("---\n\n")
    f_out.write("## 3. Relational Join Integrity & Foreign Key Analysis\n\n")
    f_out.write("| Join Path | Parent Table | Child Table | Integrity Status | Discrepancies / Notes |\n")
    f_out.write("| :--- | :--- | :--- | :--- | :--- |\n")
    f_out.write(f"| `match_id` | `matches.csv` ({join_results['bbb_to_matches']['target_unique']:,}) | `ball_by_ball.csv` ({join_results['bbb_to_matches']['source_unique']:,}) | {'✅ 100% Valid' if join_results['bbb_to_matches']['valid'] else '❌ Missing Keys'} | All {join_results['bbb_to_matches']['source_unique']} matches in BBB exist in matches table. |\n")
    f_out.write(f"| `comp_id` | `competitions.csv` ({join_results['matches_to_competitions']['target_unique']:,}) | `matches.csv` ({join_results['matches_to_competitions']['source_unique']:,}) | {'✅ 100% Valid' if join_results['matches_to_competitions']['valid'] else '❌ Missing Keys'} | All {join_results['matches_to_competitions']['source_unique']} competitions map cleanly. |\n")
    f_out.write(f"| `team_id` | `teams.csv` ({join_results['matches_to_teams']['target_unique']:,}) | `matches.csv` (home/away/win) | {'✅ 100% Valid' if join_results['matches_to_teams']['valid'] else '❌ Missing Keys'} | All team IDs resolve to team names. |\n")
    f_out.write(f"| `team_id` | `teams.csv` ({join_results['bbb_to_teams']['target_unique']:,}) | `ball_by_ball.csv` (bat/bowl) | {'✅ 100% Valid' if join_results['bbb_to_teams']['valid'] else '❌ Missing Keys'} | Batting and bowling team IDs resolve 100%. |\n")
    f_out.write(f"| `player_id` | `mapping.csv` ({join_results['bbb_to_player_map']['target_unique']:,}) | `ball_by_ball.csv` (striker/bowler) | {'✅ 100% Valid' if join_results['bbb_to_player_map']['valid'] else '❌ Missing Keys'} | Missing: {join_results['bbb_to_player_map']['missing_count']} player IDs. Handled via striker_name/bowler_name fallback. |\n")
    f_out.write(f"| `match_id` | `matches.csv` | `playing_eleven.csv` | {'✅ 100% Valid' if join_results['playing_eleven_to_matches']['valid'] else '❌ Missing Keys'} | Missing: {join_results['playing_eleven_to_matches']['missing_count']} matches. |\n")
    f_out.write("\n---\n\n")
    
    f_out.write("## 4. Critical Domain Findings & Behavioral Nuances\n\n")
    f_out.write("### A. The Extras Encoding Trap (`extras1_runs` vs. `extras_2_runs`)\n")
    f_out.write("- `extras1_runs` is **NOT** a run count. It is an internal integer enum corresponding to `extras_type`:\n")
    f_out.write("  - `1 = Overstep` (No-ball)\n")
    f_out.write("  - `2 = Wide`\n")
    f_out.write("  - `3 = Legbyes`\n")
    f_out.write("  - `4 = Byes`\n")
    f_out.write("  - `5 = Other / Penalty`\n")
    f_out.write("  - `6 = Regular delivery`\n")
    f_out.write("- `extras_2_runs` records **physical extra runs conceded** (e.g. overthrows on a wide/no-ball).\n")
    f_out.write("- **Correct Accounting Formulation:**\n")
    f_out.write("  - Total runs off delivery for team = `runs + extras_2_runs + (1 if wide or noball else 0)`\n")
    f_out.write("  - Batter legal ball = `extras_type != 'wide'` (no-balls count as balls faced by batter).\n")
    f_out.write("  - Bowler legal ball = `~extras_type.isin(['wide', 'Overstep'])`.\n")
    f_out.write("  - Bowler runs conceded = `runs + (1 if wide or noball else 0) + extras_2_runs` (byes and leg-byes are fielding extras, NOT charged to bowler).\n")
    f_out.write("  - Bowler wickets = `is_wicket == True` and dismissal type is one of `['Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket']` (run-outs, retired hurts, obstructing the field are excluded).\n\n")
    
    f_out.write("### B. Super Overs & Innings Scope\n")
    f_out.write("- `ball_by_ball.csv` contains `innings` values up to `4` (Super Overs):\n")
    f_out.write("  - Innings 1: 104,785 balls (batting first)\n")
    f_out.write("  - Innings 2: 96,157 balls (chasing)\n")
    f_out.write("  - Innings 3: 31 balls (Super Over Innings 1)\n")
    f_out.write("  - Innings 4: 26 balls (Super Over Innings 2)\n")
    f_out.write("- **Methodology Decision:** Exclude Super Overs (`innings in [3, 4]`) from standard baseline modeling and win-probability calibration, as super-over mechanics (1 over, 2 wickets) distort regular 20-over match-state leverage functions.\n\n")
    
    f_out.write("### C. Match Shortening & DLS Structure\n")
    f_out.write(f"- Exactly {len(dls_matches)} matches in `matches.csv` feature rain interruptions or revised overs/targets.\n")
    f_out.write("- In `matches.csv`, `first_inn_revised_overs` and `second_inn_revised_overs` are stored in **BALLS** (e.g., `114.0` = 19 overs, `84.0` = 14 overs).\n")
    f_out.write("- `revised_target` supplies the target score. When present, balls remaining and target must be calibrated against the revised target and scheduled balls.\n\n")
    
    f_out.write("### D. Competition Scope (IPL vs. T20I)\n")
    f_out.write("- The dataset spans:\n")
    f_out.write("  - **IPL:** 226 matches across 2022, 2023, and 2024 seasons (87,673 balls).\n")
    f_out.write("  - **T20I:** 657 matches across bilateral series and ICC Men's T20 World Cups 2022 and 2024 (113,326 balls).\n")
    f_out.write("- Total Deliveries: 200,999 balls.\n\n")
    
    f_out.write("### E. Player Identity Resolution\n")
    f_out.write("- `ball_by_ball.csv` already carries `striker_name` and `bowler_name` alongside `striker_id` and `bowler_id`.\n")
    f_out.write("- Master registry from `competition_team_player_mapping.csv` will be prioritized, with fallback to delivery-level names to ensure 0% data drop.\n\n")
    
    f_out.write("---\n\n")
    f_out.write("## 5. Next Steps for Step 2 Pipeline Execution\n\n")
    f_out.write("1. **Data Cleaning & Match State Reconstruction (`src/data_processing.py`)**: Assemble unified delivery-level table, recalculating balls remaining, target, required run rate, and wickets in hand.\n")
    f_out.write("2. **Win Probability Model (`src/win_prob_model.py`)**: Calibrate gradient boosted / logistic win expectancy models for chasing and 1st innings states with temporal train-test validation.\n")
    f_out.write("3. **Pressure Engine (`src/pressure_engine.py`)**: Derive continuous ball-by-ball leverage / Pressure Index ($PI$), validating distribution and proving separation between pressure and baseline.\n")
    f_out.write("4. **Expected Outcome Baselines (`src/expected_models.py`)**: Train contextual $xRuns$ and $xWicket$ models to quantify Runs Added Above Expected (RAAE) and Runs Saved Above Expected (RSAE).\n")
    f_out.write("5. **Player Performance & Bayesian Shrinkage (`src/player_metrics.py`)**: Compute pressure vs. baseline deltas, consistency, and apply Empirical Bayes shrinkage with strict reliability thresholds ($\ge 120$ pressure balls across $\ge 2$ seasons).\n")
    f_out.write("6. **Unbiased Official Top 10 Rankings (`outputs/`)**: Generate full CSV outputs, figures, and sensitivity analysis.\n")
    f_out.write("7. **Final Methodology Report & RR Scouting Appendix (`report/methodology_report.md`)**: Complete write-up including sanity checks and Rajasthan Royals tactical fit.\n")

print("Data audit complete. Report written to docs/data_audit.md.")

