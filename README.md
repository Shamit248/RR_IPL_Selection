# Rajasthan Royals IPL 2027: Pressure-Based Recruitment Intelligence System

A data-driven cricket analytics and machine learning system engineered to identify which players best solve Rajasthan Royals' actual weaknesses from IPL 2026, with rigorous focus on **performance under pressure, Bayesian reliability, role fit, availability likelihood, and value-for-money**.

---

## ⚡ Quick Start: How to Run

### Option 1: Fast Recruitment Pipeline (Recommended, ~5 seconds)
To run the eligibility screening, uncapped scouting, unified capped+uncapped rankings, strategic matrix, and QA audit using the preprocessed pressure metrics:

```powershell
python run_pipeline.py --recruitment
```

### Option 2: Table Verification & Integrity Audit (Instant)
To run an automated audit verifying schema integrity and confirming **0 NaNs** across all 8 final output tables:

```powershell
python run_pipeline.py --verify
```

### Option 3: Full End-to-End Pipeline from Raw Data (~2-3 minutes)
To execute every phase from raw CSV parsing and ball-by-ball match reconstruction to machine learning validation and final report generation:

```powershell
python run_pipeline.py --all
```

---

## 📋 Step-by-Step Manual Execution

If you prefer executing individual pipeline phases independently in Windows PowerShell:

| Stage | Script | Purpose | Output Files |
| :--- | :--- | :--- | :--- |
| **Phase 1** | `python phase1_audit.py` | Data integrity audit of 6 raw CSVs | Console summary |
| **Phase 2–7** | `python pipeline_p2_matchstate_pressure.py` | Ball-by-ball reconstruction & 6-variable Pressure Index | `results/pressure_features.csv` |
| **Phase 8** | `python pipeline_p3_player_metrics.py` | Player baseline vs pressure metrics & Bayesian reliability | `results/pressure_player_metrics.csv`, `results/player_reliability.csv` |
| **Phase 9** | `python pipeline_p4_model_rr_weakness.py` | Temporal ML validation & RR 2026 weakness diagnosis | `results/rr_weaknesses.csv`, `results/model_evaluation_metrics.csv` |
| **Phase 10** | `python pipeline_p5_fit_rankings.py` | Weighted player-weakness fit scoring | `results/player_fit_scores.csv` |
| **Phase 11** | `python pipeline_p6_charts_report.py` | 10 publication charts & markdown summary | `results/charts/*.png` |
| **Eligibility** | `python build_player_status.py` | Classifies 1,217 players into active/retired/contracted | `results/player_status.csv` |
| **Dual Ranks** | `python generate_dual_rankings.py` | Historical vs Active Eligible Top 10 rankings | `results/ipl2027_eligible_top10_batters.csv` |
| **Uncapped** | `python build_uncapped_recruitment_system.py` | High-value uncapped Indian talents solving RR gaps | `results/uncapped_ipl2027_top10.csv`, `results/uncapped_ipl2027_candidate_pool.csv` |
| **Final Ranks**| `python build_final_recruitment_rankings.py` | Capped + Uncapped Unified recruitment rankings | `results/rr_ipl2027_final_top10.csv`, `results/rr_ipl2027_top20.csv` |
| **Master Rep** | `python update_report_master_recruitment.py` | Builds comprehensive 900+ line master executive report | `results/final_report.md` |
| **QA Audit**   | `python verify_final_tables.py` | Verifies data integrity & checks for zero NaNs | Console audit report |

---

## 📂 Project Architecture

```text
RR_IPL_Selection/
├── 6af3166e7b922_data_pack/               # Raw IPL & T20 datasets (2022 onwards)
│   ├── ball_by_ball.csv                   # Ball-by-ball match events
│   ├── matches.csv                        # Match metadata & results
│   ├── competitions.csv                   # Tournament definitions
│   ├── teams.csv                          # Franchise & national teams
│   ├── playing_eleven.csv                 # Match team sheets
│   └── competition_team_player_mapping.csv# Player-squad mappings
│
├── results/                               # Generated analytical outputs
│   ├── rr_ipl2027_final_top10.csv         # Top 10 Combined Realistic Targets
│   ├── rr_ipl2027_top20.csv               # Top 20 Combined External Targets
│   ├── rr_ipl2027_capped_top10.csv        # Top 10 Capped Targets
│   ├── rr_ipl2027_uncapped_top10.csv      # Top 10 Uncapped Targets
│   ├── rr_ipl2027_role_targets.csv        # Role-wise fixes for RR 2026 weaknesses
│   ├── rr_ipl2027_value_upside_matrix.csv # 2x2 Value vs Upside Strategic Matrix
│   ├── player_status.csv                  # 1,217 cataloged players with eligibility
│   ├── final_report.md                    # Comprehensive master analytics report
│   └── charts/                            # 10 High-res diagnostic figures
│
├── run_pipeline.py                        # Master CLI pipeline runner
├── verify_final_tables.py                 # Automated zero-NaN verification
└── README.md                              # Pipeline documentation
```

---

## 🏆 Key Findings & Recommended Recruitment Targets

### Top 1 Overall Recommendation: Ashutosh Sharma (Uncapped Indian Finisher)
* **Final Recruitment Fit Score**: `74.82` (1st overall among external candidates)
* **Pressure Performance Score**: `85.00` | **Availability Probability**: `0.80`
* **Direct Weakness Solved**: Eliminates RR's **40.95% dot ball rate in high RRR chases** and sub-par death-over boundary rate (20.64%).
* **Pressure Metric**: 214.29 strike rate in death overs under extreme pressure; performs +35.2 strike rate points above neutral baseline.

### Role-Wise Solutions for RR IPL 2026 Weaknesses:
1. **Death Bowling Weakness (0.40 wkts/over vs 0.52 par)**:
   * *Best Overseas*: Jamie Overton (Fit: 69.12)
   * *Best Uncapped*: Sakib Hussain (Fit: 64.52)
2. **Finishing & High RRR Chases (40.95% dots vs 34.47% par)**:
   * *Best Uncapped*: Ashutosh Sharma (Fit: 74.82)
   * *Best Overseas*: Tim David (Fit: 74.46)
3. **Middle-Order Spin Counter (31.67% middle dots vs 29.53% par)**:
   * *Best Capped*: Naman Dhir (Fit: 73.55)
   * *Best Uncapped*: Mahipal Lomror (Fit: 65.24)
4. **Attacking Spin & High RRR Bowling (0.33 wkts/over vs 0.38 par)**:
   * *Best Targets*: Krishnappa Gowtham (Fit: 64.91), Suyash Sharma (Fit: 61.34)
5. **Left-Handed Batter Vulnerability (10.28 economy vs 9.60 par)**:
   * *Best Target*: Gurjapneet Singh (Left-arm pace angle, Fit: 62.46)
6. **Powerplay Bowling Seam Penetration (27.38% boundary vs 26.74% par)**:
   * *Best Targets*: Deepak Chahar (Fit: 63.88), Vaibhav Arora (Fit: 62.15)

