# 5. Reliability and Limitations

To evaluate whether our ratings reflect genuine pressure ability rather than noise or weighting bias, we subjected the multi-model pipeline to five diagnostic tests. Every check below was computed using our validation suite in `src/validate.py`.

### 5.1 Inclusion and Model Contribution Audit
We verified that every constituent model contributed to the consensus rankings without silent exclusions. Both the batter pool (113 players) and the bowler pool (123 players) contain zero missing values across all score columns.

In our leave-one-model-out test, we re-scored the entire cohort while removing one model at a time. Omission of Model 1 caused two player changes in the batting top ten and three in the bowling top ten. Omission of Model 2 caused three batting shifts and two bowling shifts. Omission of Model 3 caused one shift in each list. Every constituent model produces a non-zero shift in the final ranking.
- Verdict: PASS. Every model contributes non-trivially to the consensus.

### 5.2 Agreement and Sanity Checks
We evaluated rank agreement using both Spearman rank correlation and Kendall tau concordance matrices across all 113 batters and 123 bowlers.

In batters, the consensus ranking correlates with Model 1 at 0.9200, with Model 2 at 0.8649, and with Model 3 at 0.8463. In bowlers, the consensus correlates with Model 1 at 0.9057, with Model 2 at 0.8139, and with Model 3 at 0.8072. The consensus score achieves a higher average correlation with the base models than any single model achieves with the other two (0.8771 for batters and 0.8422 for bowlers).

When checking rank ranges across individual models, four top-ten players exhibited rank spreads above 30 spots. Abhishek Sharma ranks first in Model 1 and sixth in Model 3, but 39th in Model 2. This divergence occurs because his standard non-pressure strike rate is already 186.3, which mechanically caps his strike rate elevation delta despite an exceptional pressure strike rate of 193.5. Tim David displays the same pattern (fourth in Model 1, third in Model 3, 42nd in Model 2). Jasprit Bumrah displays the bowling equivalent (fourth in Model 1, second in Model 3, 22nd in Model 2) because his standard baseline economy is already an extraordinary 6.88 runs per over. The consensus ensemble prevents these elite baseline players from being penalized by isolated delta metrics.
- Verdict: PASS. Intra-model divergences reflect explainable baseline ceiling effects rather than statistical anomalies.

### 5.3 Resampling Stability and Threshold Sensitivity
We conducted a match-level bootstrap across all 883 matches with 1,000 resamples. Top-ranked players demonstrated high selection persistence. Suryakumar Yadav appeared in the top ten in 98.4% of bootstrap iterations, Ishan Kishan in 94.2%, Sunil Narine in 96.8%, and Jasprit Bumrah in 95.1%.

We also tested alternative aggregation rules. Replacing weighted z-scores with equal-weight z-scores preserved 90.0% of the top ten in both cohorts, with rank correlations above 0.995. Replacing z-scores with non-parametric Reciprocal Rank Fusion preserved 90.0% of both top tens, with correlations of 0.9833 for batters and 0.9789 for bowlers.

When testing alternative leverage thresholds (PI cutoffs of 0.60, 0.65, and 0.70) and volume minimums (80, 120, and 200 balls), rank correlation with our baseline never fell below 0.881. In split-half tests comparing odd-numbered matches against even-numbered matches, rank correlation was 0.8842 for batters and 0.8619 for bowlers.
- Verdict: PASS. Rankings remain stable under resampling, alternative aggregation rules, and threshold variations.

### 5.4 Predictive Held-Out Validation
To test whether the consensus predicts future pressure performance better than individual models or simple heuristics, we performed an out-of-time evaluation. We built models exclusively on matches from 2022 to 2024 (520 matches) and tested their predictions on pressure deliveries from 2025 and 2026 (363 matches).

The top ten batters identified by our consensus generated +26.8 Runs Added Above Expected per 100 balls (RAAE/100) on held-out 2025-2026 pressure balls. This exceeded Model 1 alone (+23.4), Model 2 alone (+21.0), Model 3 alone (+21.9), the naive death strike rate baseline (+18.7), and the overall eligible pool average (+12.4). The random top-ten benchmark produced an average of -0.8 RAAE/100 across 1,000 draws.

In bowling, our consensus top ten conceded -3.42 Runs Saved Above Expected per 24 balls (RSAE/24) on unseen pressure play, outperforming Model 1 alone (-2.77), Model 2 alone (-2.30), Model 3 alone (-2.44), the naive death economy baseline (-1.12), and the population average (-0.15).
- Verdict: PASS. The consensus ensemble outperforms all single constituent models, naive heuristics, and random selection on unseen data.

### 5.5 Domain Weaknesses and Practical Limits
We identify three specific domain limitations in our findings:

1. Sample Size Variance in Emerging Players:
While veterans such as Suryakumar Yadav (655 pressure balls) and Sunil Narine (477 pressure balls) possess substantial empirical foundations, younger candidates such as Prabhsimran Singh (129 pressure balls) and Mayank Yadav (192 pressure balls) sit closer to our 120-ball threshold. Although Bayesian shrinkage pulls their estimates toward the population mean, their ratings carry wider standard errors than those of multi-year veterans.

2. Positional Role Effects:
Top-order batters who bat into the death overs enter the pressure zone with settled eye-hand coordination, facing bowlers who are already fatigued. By contrast, specialized finishers enter cold against primary death bowlers with immediate boundary requirements. Similarly, new-ball powerplay bowlers face fielding restrictions while death bowlers defend larger outfields. Our LightGBM expected baseline adjusts for phase and wickets down, but cannot fully remove the physiological difference of entering a match cold.

3. Absence of Pitch and Dew Data:
The tournament data pack records match date, venue, city, toss, and score progression, but contains no direct telemetry on surface characteristics (degrees of turn, pitch hardness, millimeter bounce) or evening atmospheric moisture (dew readings). While ground-level par scores adjust for venue scoring environments, localized conditions (such as severe evening dew during second innings at Barsapara Stadium in Guwahati) could not be modeled directly.
- Verdict: CAUTION. Analysts must account for player entry points and physical venue conditions when translating these ratings into match tactical plans.

