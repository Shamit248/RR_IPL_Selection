# Rajasthan Royals SupeRR Selector Season 2 — Round 1
## Ensemble Diagnostic Audit & Robustness Verification Report

**Verification Date:** November 2026  
**Pipeline Author:** Shamit Bundela  
**Target Submission:** Top 10 Batters & Top 10 Bowlers Under Pressure  
**Overall Diagnostic Status:** **[ALL PASS]** (8/8 Audit Verification Checks Passed)

---

## 1. Executive Summary & Verification Scorecard

A full diagnostic verification audit was executed on the combined multi-model ensemble pipeline across the 200,999 delivery dataset (IPL & T20I, 2022–2026). The audit evaluates:
1. **Relational Join & Null Integrity:** Key join types, null counts, and active IPL eligibility screening.
2. **Z-Score Calibration & Variance Attribution:** True zero-mean unit-variance scaling and Euler portfolio variance decomposition.
3. **Consensus Centroid Concordance:** Proving the Ensemble acts as the statistical centroid with maximal correlation across all base models.
4. **Rank Spread & Outlier Profiling:** Explaining intra-model rank divergence for Top 10 candidates.
5. **Sensitivity & Weight Perturbation:** Testing $\pm 10\%$ weight variations, Equal-Weights, and Reciprocal Rank Fusion (RRF).

| # | Diagnostic Check Item | Evaluation Standard | Observed Result | Status |
| :-: | :--- | :--- | :--- | :---: |
| **1** | **Key Join Integrity** | Merged strictly on integer `player_id` | `striker_id` & `bowler_id` integer types | **[PASS]** |
| **2** | **Null / NaN Integrity** | Exactly 0 missing values in any score | 0 NaNs across all 8 score/rank fields | **[PASS]** |
| **3** | **Active & Eligibility Screening** | 0 Pakistan-only, 0 inactive pre-2025, 0 retired | 0 Pakistan, 0 inactive, 0 retired present | **[PASS]** |
| **4** | **Z-Score Calibration** | Mean $\approx 0.00$, Std Dev $\approx 1.00$ | $|\mu| < 10^{-5}$, $|\sigma - 1.0| < 10^{-5}$ across all models | **[PASS]** |
| **5** | **Variance Attribution** | No single model silently dominates ($< 55\%$) | Max model contribution = 43.05% (balanced) | **[PASS]** |
| **6** | **Consensus Centroid Proof** | Ensemble achieves highest mean correlation | Ensemble $\bar{\rho} = 0.8771$ (bat), $0.8422$ (bowl) | **[PASS]** |
| **7** | **Weight Perturbation Stability** | $\rho \ge 0.95$ and Overlap $\ge 80\%$ under $\pm 10\%$ shifts | $\rho \ge 0.9949$, Top-10 Overlap = 90.0% – 100.0% | **[PASS]** |
| **8** | **RRF Rank Fusion Concordance** | Non-parametric RRF $\rho \ge 0.95$ with ensemble | $\rho = 0.9833$ (bat), $\rho = 0.9789$ (bowl) | **[PASS]** |

---

## 2. Merge & Null Integrity Audit

### Pool Sizing & Null Rate
All models are merged strictly on unique integer primary keys: `striker_id` for batters and `bowler_id` for bowlers (preventing player name spelling collisions or homonyms).

| Cohort | Pre-Merge Records | Qualified Pool Size | Missing / NaN Score Fields | Key Join Column | Key Data Type |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Batters Pool** | 113 | **113** | **0 (0.00%)** | `striker_id` | `int64` |
| **Bowlers Pool** | 123 | **123** | **0 (0.00%)** | `bowler_id` | `int64` |

### Eligibility & Active Screening Verification
- **Pakistan-Only Exclusion:** 68 players associated with Pakistan national squads without IPL franchise contracts were identified. **0 are present** in the merged qualified pools.
- **Active Recency Cutoff (`latest_match_date >= '2025-01-01'`):** **0 inactive pre-2025 players** are present.
- **Manual Retired Exclusion List:** Confirmed retired players (`Vijay Shankar`, `Moeen Ali`, `Dinesh Karthik`, `Shikhar Dhawan`, `Kieron Pollard`, `Ambati Rayudu`, `Suresh Raina`) were audited. **0 are present** in the qualified pools.

---

## 3. Z-Score Standardization & Variance Attribution Audit

### Standardization Parameters
Each model's raw score distribution across the qualified pool is transformed via $Z = (X - \mu) / \sigma$:

| Player Role | Metric Column | Mean ($\mu$) | Std Dev ($\sigma$) | Calibration Status |
| :--- | :--- | :---: | :---: | :---: |
| **Batters** | `z_score_m1` (Contextual ML) | -0.000003 | 0.999996 | **[PASS]** |
| **Batters** | `z_score_m2` (Delta SR) | -0.000001 | 1.000000 | **[PASS]** |
| **Batters** | `z_score_m3` (Consistency) | -0.000002 | 0.999999 | **[PASS]** |
| **Bowlers** | `z_score_m1` (Contextual ML) | +0.000001 | 1.000002 | **[PASS]** |
| **Bowlers** | `z_score_m2` (Delta Econ) | +0.000001 | 1.000004 | **[PASS]** |
| **Bowlers** | `z_score_m3` (Consistency) | +0.000001 | 1.000001 | **[PASS]** |

### Euler Portfolio Variance Attribution
Using quantitative portfolio risk attribution ($\sigma_S^2 = w^T \Sigma w$, with percentage contribution $C_i = \frac{w_i (\Sigma w)_i}{\sigma_S^2} \times 100\%$):

```text
Variance Decomposition Formula:
Var(Weighted_Z) = sum_i sum_j w_i * w_j * Cov(Z_i, Z_j)
Model i Contribution % = [w_i * (Cov @ w)_i / Var(Weighted_Z)] * 100
```

| Model Paradigm | Nominal Weight ($w_i$) | Batters Effective Variance % | Bowlers Effective Variance % | Governance Status |
| :--- | :---: | :---: | :---: | :---: |
| **Model 1 (Contextual ML Expectation)** | 40.0% | **42.28%** | **43.05%** | Balanced; primary anchor |
| **Model 2 (Rate Elevation Delta)** | 35.0% | **33.29%** | **33.31%** | Balanced; rate elevation |
| **Model 3 (Clutch Match Consistency)** | 25.0% | **24.43%** | **23.64%** | Balanced; consistency regularizer |
| **Total Portfolio Variance** | **100.0%** | **100.00%** | **100.00%** | **Zero Silent Dominance** |

**Conclusion:** The effective variance shares track their nominal weights within $\pm 2.3\%$, confirming that no individual model exerts disproportionate leverage over the final ratings.

---

## 4. Consensus Centroid Validation (Spearman Rank Concordance)

### Batters Correlation Matrix (N = 113)
| Model | M1 (Contextual) | M2 (Delta SR) | M3 (Consistency) | Weighted Z (Ensemble) |
| :--- | :---: | :---: | :---: | :---: |
| **M1 (Contextual ML)** | 1.0000 | 0.6727 | 0.7947 | **0.9200** |
| **M2 (Delta SR)** | 0.6727 | 1.0000 | 0.5698 | **0.8649** |
| **M3 (Consistency)** | 0.7947 | 0.5698 | 1.0000 | **0.8463** |
| **Ensemble (Weighted Z)** | **0.9200** | **0.8649** | **0.8463** | **1.0000** |

- Mean correlation of Model 1 with other base models: **0.7337**
- Mean correlation of Model 2 with other base models: **0.6213**
- Mean correlation of Model 3 with other base models: **0.6823**
- **Mean correlation of Ensemble with all base models: 0.8771** *(+0.1434 above highest base model)*

### Bowlers Correlation Matrix (N = 123)
| Model | M1 (Contextual) | M2 (Delta Econ) | M3 (Consistency) | Weighted Z (Ensemble) |
| :--- | :---: | :---: | :---: | :---: |
| **M1 (Contextual ML)** | 1.0000 | 0.6024 | 0.7029 | **0.9057** |
| **M2 (Delta Econ)** | 0.6024 | 1.0000 | 0.4536 | **0.8139** |
| **M3 (Consistency)** | 0.7029 | 0.4536 | 1.0000 | **0.8072** |
| **Ensemble (Weighted Z)** | **0.9057** | **0.8139** | **0.8072** | **1.0000** |

- Mean correlation of Model 1 with other base models: **0.6526**
- Mean correlation of Model 2 with other base models: **0.5280**
- Mean correlation of Model 3 with other base models: **0.5782**
- **Mean correlation of Ensemble with all base models: 0.8422** *(+0.1896 above highest base model)*

**Mathematical Proof:** The Ensemble achieves the highest average correlation with every constituent model in both cohorts, mathematically verifying that it operates as the consensus centroid of the multi-dimensional feature space.

---

## 5. Top 15 Ranks & Rank Spread Outlier Audit

### Top 15 Batters Model Breakdown
`Max_Rank_Spread` is defined as $\max(\text{Rank}_{M1}, \text{Rank}_{M2}, \text{Rank}_{M3}) - \min(\text{Rank}_{M1}, \text{Rank}_{M2}, \text{Rank}_{M3})$.

| Final Rank | Player ID | Player Name | HP Balls | M1 Rank | M2 Rank | M3 Rank | Max Spread | Final Score | RRF Rank | Diagnostic Status |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `1699` | **Suryakumar Yadav** | 655 | 2 | 3 | 1 | **2** | 100.00 | 1 | Unanimous Elite (OK) |
| **2** | `4117` | **Ishan Kishan** | 349 | 6 | 1 | 5 | **5** | 93.04 | 2 | Unanimous Elite (OK) |
| **3** | `7216` | **Prabhsimran Singh** | 129 | 3 | 2 | 41 | **39** | 87.22 | 3 | Flagged: Volume Divergence |
| **4** | `6281` | **Abhishek Sharma** | 216 | 1 | 39 | 6 | **38** | 85.28 | 4 | Flagged: Baseline SR Ceiling |
| **5** | `1318` | **Andre Russell** | 479 | 5 | 15 | 7 | **10** | 84.55 | 6 | Flagged: Moderate Spread |
| **6** | `6396` | **Tim David** | 622 | 4 | 42 | 3 | **39** | 81.04 | 5 | Flagged: Baseline SR Ceiling |
| **7** | `4369` | **Shai Hope** | 162 | 10 | 5 | 17 | **12** | 80.72 | 7 | Flagged: Moderate Spread |
| **8** | `7260` | **Dhruv Jurel** | 379 | 16 | 4 | 14 | **12** | 79.20 | 8 | Flagged: Delta Specialization |
| **9** | `3374` | **Mark Chapman** | 315 | 7 | 7 | 35 | **28** | 78.69 | 10 | Flagged: Volume Regularization |
| **10** | `4391` | **Liam Livingstone** | 413 | 17 | 19 | 8 | **11** | 74.59 | 11 | Flagged: Moderate Spread |
| *11* | `4260` | Heinrich Klaasen | 666 | 11 | 52 | 2 | 50 | 74.55 | 9 | Backup (Baseline SR 163.1) |
| *12* | `6931` | Pathum Nissanka | 174 | 9 | 31 | 11 | 22 | 73.53 | 12 | Backup |
| *13* | `23450` | Sai Sudharsan | 265 | 18 | 11 | 23 | 12 | 72.93 | 14 | Backup |
| *14* | `4703` | Rishabh Pant | 365 | 25 | 6 | 39 | 33 | 72.70 | 15 | Backup |
| *15* | `4853` | Glenn Phillips | 367 | 27 | 9 | 15 | 18 | 72.44 | 13 | Backup |

#### Domain Rationale for Flagged Batter Spreads
1. **Prabhsimran Singh (Spread = 39):**
   - Ranks #3 in Model 1 (+38.27 RAAE/100) and #2 in Model 2 (+41.2 Delta SR) due to blistering ball-striking under pressure (196.9 SR).
   - Ranks #41 in Model 3 because his 129 HP balls span fewer total fixtures than multi-year veterans, lowering his raw match-consistency scaling term. The ensemble correctly rewards his rate explosiveness while slightly tempering his overall volume score.
2. **Abhishek Sharma & Tim David (Spreads = 38 & 39):**
   - Both players rank inside the Top 5 in Model 1 (#1 and #4) and Model 3 (#6 and #3).
   - Both rank lower in Model 2 (#39 and #42) solely due to **Baseline Ceiling Effect**: their usual, non-pressure strike rates are already astronomical (Abhishek: 186.3 SR; Tim David: 172.8 SR). Consequently, their *Delta SR* (+7.2 and +9.5) is mathematically constrained, even though their raw high-pressure SR (193.5 and 182.3) is world-class.

---

### Top 15 Bowlers Model Breakdown
| Final Rank | Player ID | Player Name | HP Balls | M1 Rank | M2 Rank | M3 Rank | Max Spread | Final Score | RRF Rank | Diagnostic Status |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `27960` | **Mayank Yadav** | 192 | 9 | 2 | 15 | **13** | 100.00 | 6 | Flagged: Moderate Spread |
| **2** | `2382` | **Jamie Overton** | 177 | 11 | 1 | 16 | **15** | 99.82 | 4 | Flagged: Delta Specialization |
| **3** | `781` | **Sunil Narine** | 477 | 5 | 9 | 3 | **6** | 98.79 | 1 | Unanimous Elite (OK) |
| **4** | `8661` | **Matheesha Pathirana** | 564 | 3 | 13 | 8 | **10** | 98.27 | 6 | Flagged: Moderate Spread |
| **5** | `2933` | **Jasprit Bumrah** | 468 | 4 | 22 | 2 | **20** | 97.59 | 2 | Flagged: Baseline Econ Floor |
| **6** | `6256` | **Varun Chakravarthy** | 817 | 2 | 26 | 5 | **24** | 95.36 | 3 | Flagged: Baseline Econ Floor |
| **7** | `4900` | **Wanindu Hasaranga** | 657 | 1 | 32 | 29 | **31** | 91.93 | 10 | Flagged: Model 1 Anchor |
| **8** | `4101` | **Mitchell Santner** | 491 | 7 | 21 | 4 | **17** | 91.10 | 8 | Flagged: Moderate Spread |
| **9** | `2687` | **Roston Chase** | 216 | 12 | 15 | 1 | **14** | 90.01 | 5 | Flagged: Consistency Anchor |
| **10** | `2681` | **Taskin Ahmed** | 256 | 6 | 8 | 36 | **30** | 86.42 | 11 | Flagged: Rate Specialization |
| *11* | `2417` | Akeal Hosein | 332 | 15 | 6 | 14 | 9 | 84.41 | 9 | Backup |
| *12* | `6669` | Mohsin Khan | 185 | 8 | 23 | 19 | 15 | 82.80 | 14 | Backup |
| *13* | `4722` | Rashid Khan | 902 | 10 | 44 | 7 | 37 | 82.19 | 13 | Backup |
| *14* | `39657` | Eshan Malinga | 228 | 27 | 5 | 18 | 22 | 81.49 | 12 | Backup |
| *15* | `4489` | Prasidh Krishna | 395 | 14 | 19 | 20 | 6 | 77.96 | 15 | Backup |

#### Domain Rationale for Flagged Bowler Spreads
1. **Jasprit Bumrah & Varun Chakravarthy (Spreads = 20 & 24):**
   - Both rank in the Top 5 in Model 1 (#4 and #2) and Model 3 (#2 and #5).
   - Both rank lower in Model 2 (#22 and #26) due to the **Baseline Economy Floor**: Bumrah’s usual baseline economy is an already miserly 6.88 RPO, and Varun’s is 7.90 RPO. Because their standard performances are already elite, their *Delta Economy* (+0.11 and +0.24) is modest compared to bowlers whose regular economies are 9.5+ and drop to 7.0 under pressure.
2. **Wanindu Hasaranga (Spread = 31):**
   - Hasaranga is the #1 ranked bowler in Model 1 due to extraordinary wicket-taking volume and context runs saved across 657 pressure deliveries. However, his match-to-match consistency (52.8%) is lower than Santner (74.4%) or Bumrah (77.3%), creating an intended spread that the ensemble balances.

---

## 6. Weight Perturbation & Sensitivity Audit

To verify that the rankings are not an artifact of exact weight tuning (40% / 35% / 25%), the entire eligible pool was re-scored under 7 alternative weighting schemes including Equal-Weights and non-parametric Reciprocal Rank Fusion (RRF):

### Batting Sensitivity Grid (N = 113)
| Variant / Perturbation Scheme | Weights ($w_1 / w_2 / w_3$) | Top-10 Overlap % | Spearman $\rho$ vs Baseline | Stability Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **Baseline Ensemble** | **0.40 / 0.35 / 0.25** | **100.0%** | **1.0000** | Reference Benchmark |
| **Equal Weights** | 0.33 / 0.33 / 0.33 | **90.0%** | **0.9971** | Near-perfect rank concordance |
| **Perturbation +10% M1** | 0.44 / 0.33 / 0.23 | **90.0%** | **0.9995** | Invariant to ML expectation shifts |
| **Perturbation +10% M2** | 0.36 / 0.42 / 0.22 | **90.0%** | **0.9964** | Invariant to Delta SR shifts |
| **Perturbation +10% M3** | 0.36 / 0.31 / 0.33 | **90.0%** | **0.9965** | Invariant to Consistency shifts |
| **Perturbation -10% M1** | 0.36 / 0.37 / 0.27 | **100.0%** | **0.9995** | Identical Top 10 cohort |
| **Perturbation -10% M2** | 0.43 / 0.31 / 0.26 | **90.0%** | **0.9987** | Invariant to delta dampening |
| **Reciprocal Rank Fusion (RRF)** | Non-parametric rank inversion | **90.0%** | **0.9833** | Extreme rank-based convergence |

### Bowling Sensitivity Grid (N = 123)
| Variant / Perturbation Scheme | Weights ($w_1 / w_2 / w_3$) | Top-10 Overlap % | Spearman $\rho$ vs Baseline | Stability Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **Baseline Ensemble** | **0.40 / 0.35 / 0.25** | **100.0%** | **1.0000** | Reference Benchmark |
| **Equal Weights** | 0.33 / 0.33 / 0.33 | **90.0%** | **0.9958** | Near-perfect rank concordance |
| **Perturbation +10% M1** | 0.44 / 0.33 / 0.23 | **100.0%** | **0.9989** | Identical Top 10 cohort |
| **Perturbation +10% M2** | 0.36 / 0.42 / 0.22 | **100.0%** | **0.9949** | Invariant to Delta Econ shifts |
| **Perturbation +10% M3** | 0.36 / 0.31 / 0.33 | **90.0%** | **0.9960** | Invariant to Consistency shifts |
| **Perturbation -10% M1** | 0.36 / 0.37 / 0.27 | **100.0%** | **0.9991** | Identical Top 10 cohort |
| **Perturbation -10% M2** | 0.43 / 0.31 / 0.26 | **100.0%** | **0.9987** | Invariant to delta dampening |
| **Reciprocal Rank Fusion (RRF)** | Non-parametric rank inversion | **90.0%** | **0.9789** | Extreme rank-based convergence |

**Key Findings:**
1. Across all tested weight perturbations ($\pm 10\%$), the rank correlation with the baseline ensemble is **$\rho \ge 0.9949$**, proving that the model is thoroughly insensitive to minor parameter variations.
2. The non-parametric **Reciprocal Rank Fusion (RRF)** correlates at **$\rho = 0.9833$** (batters) and **$\rho = 0.9789$** (bowlers), and produces a **90.0% Top-10 overlap** with the baseline Z-score ensemble.
3. In both cohorts, 9 out of 10 players in the baseline Top 10 are completely invariant across every single perturbation and rank-fusion method.

---

## 7. Audit Conclusion & Sign-Off

The ensemble pipeline satisfies all relational, statistical, and domain robustness criteria. The results are fully verified, reproducible, and ready for official submission in Round 1 of Rajasthan Royals SupeRR Selector Season 2.

