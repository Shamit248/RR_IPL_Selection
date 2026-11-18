# Open Items and Confirmation Log
**Competition:** Rajasthan Royals SupeRR Selector Season 2 (Round 1)  
**Author:** Shamit Bundela  
**Date:** November 2026  
**Status:** ALL DELIVERABLES GENERATED, FORMATTED & VERIFIED (PASS)

---

## 1. Resolved Enhancements (Confirmed & Implemented)
- **Embedded Figure Rendering (100% Fixed):**
  - All 5 high-resolution figures are now embedded directly in the PDF via Base64 data URIs and in DOCX via centered picture runs with captions.
  - Verification confirmed all 5 images render crisply with zero empty boxes across the 12-page document.
- **Mathematical Formulations & Alignment:**
  - Added 12 dedicated, aligned mathematical formula blocks (Equations 1 through 12) covering:
    - Eq 1: Win-probability state function
    - Eq 2: Delivery-level leverage index ($L_t$)
    - Eq 3: Normalized continuous Pressure Index ($PI_t \ge 0.65$)
    - Eq 4: Contextual expectation baselines ($xRuns_t, xWkt_t$)
    - Eq 5: Model 1 Batting Expectation (Raw RAAE/100)
    - Eq 6: Model 1 Bowling Expectation (Raw RSAE/24)
    - Eq 7: Empirical Bayes small-sample shrinkage ($K = 40.0$)
    - Eq 8: Model 2 Rate elevation deltas ($\Delta \text{SR}, \Delta \text{Econ}$)
    - Eq 9: Model 3 Match-level clutch consistency
    - Eq 10: Standardized Z-score transformation
    - Eq 11: Euler portfolio variance decomposition
    - Eq 12: Final Ensemble Score min-max scaling ($0 \text{ to } 100$)
- **End-to-End Player Selection Process (Section 3):**
  - Added an 8-stage quantitative funnel walking through:
    1. Relational Ingestion & State Reconstruction (200,999 deliveries, 883 matches, canonical integer IDs)
    2. Delivery Leverage Tagging & Partitioning ($PI \ge 0.65$, top 28.55% leverage)
    3. Cohort Qualification & Eligibility Filtering (120 HP balls, active $\ge 2025-01-01$, 113 batters & 123 bowlers qualified)
    4. Tri-Model Rating & Bayesian Shrinkage (Contextual ML, Rate Delta, Match Consistency)
    5. Cohort-Wide Z-Score Normalization ($\mu = 0.00, \sigma = 1.00$)
    6. Portfolio Weight Aggregation ($w = [0.40, 0.35, 0.25]$)
    7. Consensus Verification & Diagnostic Auditing (Centroid proof, bootstrap, out-of-sample test)
    8. Franchise Availability Partitioning & Final Submission (Dual-table split)
- **Official Top-10 Submission Lists:**
  - **Batters (IPL-Eligible):** 1. Suryakumar Yadav, 2. Ishan Kishan, 3. Prabhsimran Singh, 4. Abhishek Sharma, 5. Andre Russell, 6. Tim David, 7. Shai Hope, 8. Dhruv Jurel (RR - Retained), 9. Liam Livingstone, 10. Heinrich Klaasen. (Immediate Backups: #11 Pathum Nissanka, #12 Sai Sudharsan, #13 Rishabh Pant).
  - **Bowlers (IPL-Eligible):** 1. Mayank Yadav, 2. Jamie Overton, 3. Sunil Narine, 4. Matheesha Pathirana, 5. Jasprit Bumrah, 6. Varun Chakravarthy, 7. Wanindu Hasaranga (LSG), 8. Mitchell Santner, 9. Akeal Hosein, 10. Mohsin Khan. (Immediate Backups: #11 Rashid Khan, #12 Arshdeep Singh).
- **Official GitHub Repository Added:**
  - [https://github.com/Shamit248/RR_IPL_Selection](https://github.com/Shamit248/RR_IPL_Selection) integrated across Report Title Block, Section 5.5, and README.md.
- **Compliance Audit Scorecard:**
  - Exactly 12 pages in PDF (satisfying 10–14 page constraint).
  - 0 banned words, 0 em dashes, 0 emojis, 0 bold words in body paragraphs.
  - 100% numerical concordance with `outputs/validation/*.csv`.

---

## 2. Items for Final Review Before Upload to Unstop
1. **Unstop Dropdown Entry:**
   - Use the official IPL-eligible lists from Table E1 and Table E2 (`outputs/final_top10_batters_ipl.csv` and `outputs/final_top10_bowlers_ipl.csv`).
   - If an unlisted international appears in your manual dropdown search, consult the unfiltered reference list (`outputs/final_top10_batters_all.csv` and `outputs/final_top10_bowlers_all.csv`) where Mark Chapman (Batters #9), Roston Chase (Bowlers #9), and Taskin Ahmed (Bowlers #10) are recorded.
2. **Analytical Limitations Acknowledgment:**
   - Section 5.5 explicitly notes that pitch telemetry (turn degrees, millimeter bounce) and evening dew sensor readings are not recorded in tournament scorecards, explaining why venue-level par scores serve as the empirical proxy.
3. **Rajasthan Royals Purse & Retention Data:**
   - Section 6 outlines RR's post-retention auction roadmap under the Rs 27.05 crore purse and 6 vacant slots (max 3 overseas), highlighting top targets for Role A (Finisher) and Role B (Death Pacer).
