# Data Audit Report — Rajasthan Royals SupeRR Selector Season 2 (Round 1)

**Generated on:** 2026-11-18  
**Role:** Lead Cricket Quantitative Analyst / Senior Data Scientist  
**Scope:** Comprehensive structural audit of all supplied IPL & T20I CSV files from 2022 onwards in `./data`.

---

## 1. Executive Summary & File Inventory

The dataset contains 6 primary relational CSV files capturing ball-by-ball actions, match metadata, competition definitions, team rosters, and playing elevens across the Indian Premier League (IPL) and Men's T20 Internationals (T20I) from 2022 to 2024.

| File Name | Record Count | Column Count | File Size | Primary Key / Grain | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `competitions.csv` | 141 | 4 | 0.01 MB | `comp_id` | Relational table |
| `teams.csv` | 353 | 3 | 0.01 MB | `team_id` | Relational table |
| `matches.csv` | 883 | 22 | 0.12 MB | `match_id` | Relational table |
| `playing_eleven.csv` | 28,381 | 9 | 0.92 MB | `match_id`, `player_id` | Relational table |
| `competition_team_player_mapping.csv` | 6,413 | 6 | 0.44 MB | `comp_id`, `team_id`, `player_id` | Relational table |
| `ball_by_ball.csv` | 200,999 | 33 | 39.17 MB | `match_id`, `innings`, `overid`, `over_ball_num` | Relational table |

---

## 2. Detailed Schemas, Data Types & Null Profiles

### 2.1 `competitions.csv` (141 rows, 4 columns)

| Column Name | Inferred Dtype | Null Count | Null % | Unique Values | Sample Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `comp_id` | `int64` | 0 | 0.00% | 141 | `3395, 3405, 3465` |
| `comp_name` | `object` | 0 | 0.00% | 141 | `South Africa in New Zealand T20I Seri...` |
| `match_format` | `object` | 0 | 0.00% | 2 | `T20I, T20` |
| `season` | `object` | 0 | 0.00% | 8 | `2026, 2022, 2023` |

### 2.2 `teams.csv` (353 rows, 3 columns)

| Column Name | Inferred Dtype | Null Count | Null % | Unique Values | Sample Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `comp_id` | `int64` | 0 | 0.00% | 141 | `1331, 1335, 1345` |
| `team_id` | `int64` | 0 | 0.00% | 38 | `22, 28, 18` |
| `team_name` | `object` | 0 | 0.00% | 38 | `England, West Indies, India` |

### 2.3 `matches.csv` (883 rows, 22 columns)

| Column Name | Inferred Dtype | Null Count | Null % | Unique Values | Sample Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `match_id` | `int64` | 0 | 0.00% | 883 | `13511, 13512, 13513` |
| `comp_id` | `int64` | 0 | 0.00% | 138 | `1331, 1335, 1345` |
| `match_number` | `int64` | 0 | 0.00% | 75 | `1, 2, 3` |
| `match_date` | `object` | 0 | 0.00% | 686 | `2022-01-22, 2022-01-23, 2022-01-26` |
| `stage` | `object` | 0 | 0.00% | 7 | `League, Qualifier, Eliminator` |
| `venue_id` | `int64` | 0 | 0.00% | 98 | `54, 8, 44` |
| `venue_country` | `object` | 0 | 0.00% | 17 | `West Indies, India, Australia` |
| `home_team_id` | `int64` | 0 | 0.00% | 36 | `28, 18, 20` |
| `home_team` | `object` | 0 | 0.00% | 36 | `West Indies, India, Australia` |
| `away_team_id` | `int64` | 0 | 0.00% | 36 | `22, 28, 27` |
| `away_team` | `object` | 0 | 0.00% | 36 | `England, West Indies, Sri Lanka` |
| `home_team_captain_id` | `float64` | 44 | 4.98% | 89 | `494.0, 126.0, 250.0` |
| `away_team_captain_id` | `float64` | 45 | 5.10% | 98 | `478.0, 1596.0, 494.0` |
| `toss_win_team_id` | `float64` | 15 | 1.70% | 37 | `28.0, 22.0, 18.0` |
| `toss_opted` | `object` | 15 | 1.70% | 2 | `Fielding, Batting` |
| `man_of_the_match` | `int64` | 0 | 0.00% | 293 | `0, 4986, 1699` |
| `first_inn_revised_overs` | `float64` | 858 | 97.17% | 13 | `114.0, 84.0, 66.0` |
| `second_inn_revised_overs` | `float64` | 858 | 97.17% | 12 | `114.0, 42.0, 48.0` |
| `revised_target` | `float64` | 860 | 97.40% | 23 | `143.0, 56.0, 91.0` |
| `knock_out` | `int64` | 0 | 0.00% | 2 | `0, 1` |
| `win_team_id` | `float64` | 41 | 4.64% | 36 | `28.0, 22.0, 18.0` |
| `result` | `object` | 0 | 0.00% | 670 | `West Indies Won by 9 Wickets, England...` |

### 2.4 `playing_eleven.csv` (28,381 rows, 9 columns)

| Column Name | Inferred Dtype | Null Count | Null % | Unique Values | Sample Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `match_id` | `int64` | 0 | 0.00% | 880 | `13511, 13512, 13513` |
| `team_id` | `int64` | 0 | 0.00% | 38 | `22, 28, 18` |
| `player_id` | `int64` | 0 | 0.00% | 1,082 | `1187, 6273, 1210` |
| `batting_order` | `float64` | 8,678 | 30.58% | 13 | `1.0, 2.0, 3.0` |
| `is_played` | `bool` | 0 | 0.00% | 2 | `True, False` |
| `is_captain` | `object` | 8,667 | 30.54% | 2 | `False, True` |
| `is_wk` | `object` | 8,667 | 30.54% | 2 | `False, True` |
| `is_impact` | `int64` | 0 | 0.00% | 2 | `0, 1` |
| `is_impact_off` | `int64` | 0 | 0.00% | 2 | `0, 1` |

### 2.5 `competition_team_player_mapping.csv` (6,413 rows, 6 columns)

| Column Name | Inferred Dtype | Null Count | Null % | Unique Values | Sample Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `comp_id` | `int64` | 0 | 0.00% | 140 | `1331, 1335, 1345` |
| `comp_name` | `object` | 0 | 0.00% | 140 | `England in West Indies T20I Series 20...` |
| `team_id` | `int64` | 0 | 0.00% | 38 | `22, 28, 18` |
| `team_name` | `object` | 0 | 0.00% | 38 | `England, West Indies, India` |
| `player_id` | `int64` | 0 | 0.00% | 1,217 | `478, 479, 722` |
| `player_name` | `object` | 0 | 0.00% | 1,210 | `Eoin Morgan, Adil Rashid, Liam Dawson` |

### 2.6 `ball_by_ball.csv` (200,999 rows, 33 columns)

| Column Name | Inferred Dtype | Null Count | Null % | Unique Values | Sample Values |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `match_id` | `int64` | 0 | 0.00% | 867 | `13511, 13512, 13513` |
| `innings` | `int64` | 0 | 0.00% | 4 | `1, 2, 3` |
| `overid` | `int64` | 0 | 0.00% | 20 | `1, 2, 3` |
| `over_ball_num` | `int64` | 0 | 0.00% | 13 | `1, 2, 3` |
| `innings_ball_num` | `int64` | 0 | 0.00% | 136 | `1, 2, 3` |
| `batting_team_id` | `int64` | 0 | 0.00% | 38 | `22, 28, 18` |
| `bowling_team_id` | `int64` | 0 | 0.00% | 38 | `28, 22, 18` |
| `striker_id` | `int64` | 0 | 0.00% | 888 | `1187, 6273, 1596` |
| `striker_name` | `object` | 0 | 0.00% | 885 | `Jason Roy, Tom Banton, Moeen Ali` |
| `non_striker_id` | `int64` | 0 | 0.00% | 867 | `6273, 1210, 478` |
| `non_striker_name` | `object` | 0 | 0.00% | 864 | `Tom Banton, James Vince, Eoin Morgan` |
| `bowler_id` | `int64` | 0 | 0.00% | 647 | `1772, 2633, 2417` |
| `bowler_name` | `object` | 0 | 0.00% | 646 | `Sheldon Cottrell, Jason Holder, Akeal...` |
| `batting_type` | `object` | 0 | 0.00% | 2 | `RHB, LHB` |
| `bowling_type` | `object` | 0 | 0.00% | 12 | `Left-arm fast-medium, Right-arm mediu...` |
| `batting_order` | `int64` | 0 | 0.00% | 13 | `1, 2, 4` |
| `runs` | `int64` | 0 | 0.00% | 7 | `0, 6, 4` |
| `is_four` | `bool` | 0 | 0.00% | 2 | `False, True` |
| `is_six` | `bool` | 0 | 0.00% | 2 | `False, True` |
| `is_wicket` | `bool` | 0 | 0.00% | 2 | `False, True` |
| `dismissal_type_id` | `float64` | 190,118 | 94.59% | 8 | `1.0, 2.0, 5.0` |
| `dismissal_type` | `object` | 190,118 | 94.59% | 9 | `Bowled, Caught, Stump` |
| `dismissed_player_id` | `float64` | 190,107 | 94.58% | 814 | `1187.0, 6273.0, 1596.0` |
| `extras_type` | `object` | 189,167 | 94.11% | 6 | `wide, legbyes, byes` |
| `extras1_runs` | `int64` | 0 | 0.00% | 7 | `6, 2, 3` |
| `extras_2_runs` | `int64` | 0 | 0.00% | 3 | `0, 4, 1` |
| `pace_or_spin` | `object` | 0 | 0.00% | 2 | `Pace, Spin` |
| `bowl_speed` | `float64` | 0 | 0.00% | 1,033 | `0.0, 126.0, 127.0` |
| `stroke` | `object` | 6,158 | 3.06% | 30 | `Cover Drive, Flick, Square Cut` |
| `delivery_style` | `object` | 391 | 0.19% | 34 | `Inswing, Seamed In, Full Toss` |
| `over_or_around` | `object` | 407 | 0.20% | 2 | `Over, Around` |
| `on_or_off` | `object` | 0 | 0.00% | 2 | `Off-side, On-side` |
| `delivery_ist_time` | `object` | 0 | 0.00% | 200,826 | `2022-01-23 00:00:00 UTC, 2022-01-23 0...` |

---

## 3. Relational Join Integrity & Foreign Key Analysis

| Join Path | Parent Table | Child Table | Integrity Status | Discrepancies / Notes |
| :--- | :--- | :--- | :--- | :--- |
| `match_id` | `matches.csv` (883) | `ball_by_ball.csv` (867) | ✅ 100% Valid | All 867 matches in BBB exist in matches table. |
| `comp_id` | `competitions.csv` (141) | `matches.csv` (138) | ✅ 100% Valid | All 138 competitions map cleanly. |
| `team_id` | `teams.csv` (38) | `matches.csv` (home/away/win) | ✅ 100% Valid | All team IDs resolve to team names. |
| `team_id` | `teams.csv` (38) | `ball_by_ball.csv` (bat/bowl) | ✅ 100% Valid | Batting and bowling team IDs resolve 100%. |
| `player_id` | `mapping.csv` (1,217) | `ball_by_ball.csv` (striker/bowler) | ✅ 100% Valid | Missing: 0 player IDs. Handled via striker_name/bowler_name fallback. |
| `match_id` | `matches.csv` | `playing_eleven.csv` | ✅ 100% Valid | Missing: 0 matches. |

---

## 4. Critical Domain Findings & Behavioral Nuances

### A. The Extras Encoding Trap (`extras1_runs` vs. `extras_2_runs`)
- `extras1_runs` is **NOT** a run count. It is an internal integer enum corresponding to `extras_type`:
  - `1 = Overstep` (No-ball)
  - `2 = Wide`
  - `3 = Legbyes`
  - `4 = Byes`
  - `5 = Other / Penalty`
  - `6 = Regular delivery`
- `extras_2_runs` records **physical extra runs conceded** (e.g. overthrows on a wide/no-ball).
- **Correct Accounting Formulation:**
  - Total runs off delivery for team = `runs + extras_2_runs + (1 if wide or noball else 0)`
  - Batter legal ball = `extras_type != 'wide'` (no-balls count as balls faced by batter).
  - Bowler legal ball = `~extras_type.isin(['wide', 'Overstep'])`.
  - Bowler runs conceded = `runs + (1 if wide or noball else 0) + extras_2_runs` (byes and leg-byes are fielding extras, NOT charged to bowler).
  - Bowler wickets = `is_wicket == True` and dismissal type is one of `['Bowled', 'Caught', 'LBW', 'Stump', 'Hit Wicket']` (run-outs, retired hurts, obstructing the field are excluded).

### B. Super Overs & Innings Scope
- `ball_by_ball.csv` contains `innings` values up to `4` (Super Overs):
  - Innings 1: 104,785 balls (batting first)
  - Innings 2: 96,157 balls (chasing)
  - Innings 3: 31 balls (Super Over Innings 1)
  - Innings 4: 26 balls (Super Over Innings 2)
- **Methodology Decision:** Exclude Super Overs (`innings in [3, 4]`) from standard baseline modeling and win-probability calibration, as super-over mechanics (1 over, 2 wickets) distort regular 20-over match-state leverage functions.

### C. Match Shortening & DLS Structure
- Exactly 34 matches in `matches.csv` feature rain interruptions or revised overs/targets.
- In `matches.csv`, `first_inn_revised_overs` and `second_inn_revised_overs` are stored in **BALLS** (e.g., `114.0` = 19 overs, `84.0` = 14 overs).
- `revised_target` supplies the target score. When present, balls remaining and target must be calibrated against the revised target and scheduled balls.

### D. Competition Scope (IPL vs. T20I)
- The dataset spans:
  - **IPL:** 226 matches across 2022, 2023, and 2024 seasons (87,673 balls).
  - **T20I:** 657 matches across bilateral series and ICC Men's T20 World Cups 2022 and 2024 (113,326 balls).
- Total Deliveries: 200,999 balls.

### E. Player Identity Resolution
- `ball_by_ball.csv` already carries `striker_name` and `bowler_name` alongside `striker_id` and `bowler_id`.
- Master registry from `competition_team_player_mapping.csv` will be prioritized, with fallback to delivery-level names to ensure 0% data drop.

---

## 5. Next Steps for Step 2 Pipeline Execution

1. **Data Cleaning & Match State Reconstruction (`src/data_processing.py`)**: Assemble unified delivery-level table, recalculating balls remaining, target, required run rate, and wickets in hand.
2. **Win Probability Model (`src/win_prob_model.py`)**: Calibrate gradient boosted / logistic win expectancy models for chasing and 1st innings states with temporal train-test validation.
3. **Pressure Engine (`src/pressure_engine.py`)**: Derive continuous ball-by-ball leverage / Pressure Index ($PI$), validating distribution and proving separation between pressure and baseline.
4. **Expected Outcome Baselines (`src/expected_models.py`)**: Train contextual $xRuns$ and $xWicket$ models to quantify Runs Added Above Expected (RAAE) and Runs Saved Above Expected (RSAE).
5. **Player Performance & Bayesian Shrinkage (`src/player_metrics.py`)**: Compute pressure vs. baseline deltas, consistency, and apply Empirical Bayes shrinkage with strict reliability thresholds ($\ge 120$ pressure balls across $\ge 2$ seasons).
6. **Unbiased Official Top 10 Rankings (`outputs/`)**: Generate full CSV outputs, figures, and sensitivity analysis.
7. **Final Methodology Report & RR Scouting Appendix (`report/methodology_report.md`)**: Complete write-up including sanity checks and Rajasthan Royals tactical fit.
