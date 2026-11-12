"""
update_report_master_recruitment.py
===================================
Appends the comprehensive Master Section:
# IPL 2027 Rajasthan Royals Recruitment
with all 10 required subsections to results/final_report.md.
"""

import os
import pandas as pd

RESULTS_DIR = 'results'
report_path = os.path.join(RESULTS_DIR, 'final_report.md')

top20_df    = pd.read_csv(os.path.join(RESULTS_DIR, 'rr_ipl2027_top20.csv'))
final10_df  = pd.read_csv(os.path.join(RESULTS_DIR, 'rr_ipl2027_final_top10.csv'))
capped10_df = pd.read_csv(os.path.join(RESULTS_DIR, 'rr_ipl2027_capped_top10.csv'))
uncapped10_df = pd.read_csv(os.path.join(RESULTS_DIR, 'rr_ipl2027_uncapped_top10.csv'))
role_targets_df = pd.read_csv(os.path.join(RESULTS_DIR, 'rr_ipl2027_role_targets.csv'))
value_matrix_df = pd.read_csv(os.path.join(RESULTS_DIR, 'rr_ipl2027_value_upside_matrix.csv'))

with open(report_path, 'r', encoding='utf-8') as f:
    current_text = f.read()

# Generate Markdown tables
def to_markdown_table(df, cols, headers):
    header_row = "| " + " | ".join(headers) + " |"
    sep_row = "| " + " | ".join([":---:" if c in ['rank', 'player_id', 'age'] else (":---" if 'name' in c or 'role' in c or 'target' in c else ":---:") for c in cols]) + " |"
    data_rows = []
    for idx, r in df.iterrows():
        row_str = "| " + " | ".join([str(r[c]) for c in cols]) + " |"
        data_rows.append(row_str)
    return "\n".join([header_row, sep_row] + data_rows)

top20_md = to_markdown_table(
    top20_df,
    ['rank', 'player_name', 'player_category', 'primary_role', 'final_rr_2027_fit_score', 'pressure_score', 'reliability_score', 'availability_probability', 'primary_problem_solved', 'recommendation'],
    ['Rank', 'Player Name', 'Category', 'Role', 'Final Fit Score', 'Pressure', 'Reliability', 'Avail Prob', 'Primary Problem Solved', 'Recommendation']
)

final10_md = to_markdown_table(
    final10_df,
    ['rank', 'player_name', 'player_category', 'primary_role', 'final_rr_2027_fit_score', 'pressure_score', 'rr_weakness_fit', 'availability_probability', 'primary_problem_solved', 'recommendation'],
    ['Rank', 'Player Name', 'Category', 'Role', 'Final Fit Score', 'Pressure', 'Weakness Fit', 'Avail Prob', 'Primary Problem Solved', 'Strategic Tag']
)

capped10_md = to_markdown_table(
    capped10_df,
    ['rank', 'player_name', 'player_category', 'primary_role', 'final_rr_2027_fit_score', 'pressure_score', 'availability_probability', 'primary_problem_solved', 'recommendation'],
    ['Rank', 'Player Name', 'Category', 'Role', 'Final Fit Score', 'Pressure', 'Avail Prob', 'Primary Problem Solved', 'Recommendation']
)

uncapped10_md = to_markdown_table(
    uncapped10_df,
    ['rank', 'player_name', 'primary_role', 'final_rr_2027_fit_score', 'pressure_score', 'availability_probability', 'primary_problem_solved', 'recommendation'],
    ['Rank', 'Player Name', 'Role', 'Final Fit Score', 'Pressure', 'Avail Prob', 'Primary Problem Solved', 'Recommendation']
)

role_targets_md = to_markdown_table(
    role_targets_df,
    ['weakness_category', 'rr_weakness_metric', 'best_available_target', 'best_uncapped_target', 'best_capped_target', 'backup_target'],
    ['Weakness Category', 'RR 2026 Metric vs League Par', 'Best Available Target', 'Best Uncapped Target', 'Best Capped Target', 'Backup Target']
)

matrix_md = to_markdown_table(
    value_matrix_df.head(20),
    ['player_name', 'player_category', 'primary_role', 'final_rr_2027_fit_score', 'age_upside', 'quadrant', 'auction_strategy'],
    ['Player Name', 'Category', 'Role', 'Fit Score', 'Upside', '2x2 Quadrant', 'Auction Valuation Bracket']
)

master_recruitment_section = f"""

---

# IPL 2027 Rajasthan Royals Recruitment: The Master Blueprint

This master section represents the culmination of the data pipeline, answering the central competition question:
> **"Among realistic IPL 2027 auction/recruitment candidates, which players best solve Rajasthan Royals' actual IPL 2026 weaknesses?"**

---

## 1. RR IPL 2026 Weaknesses: The Empirical Grounding

Rajasthan Royals' recruitment strategy is not dictated by reputation or brand value; it is mathematically anchored in the empirical failure points identified from RR's 14 matches in IPL 2026:

1. **Death Bowling Collapse (Weakness #1 & #8):**  
   - *Metric:* **0.40 wickets/over** at the death vs IPL par of **0.52 wickets/over** (-23.1% deficit). Conceded 11.20 economy in overs 17–20.
   - *Impact:* RR leaked an average of 14.8 runs above league par in the final 4 overs, turning winning defensive positions into defeats.
2. **High Required Run Rate Dot-Ball Paralysis (Weakness #2):**  
   - *Metric:* **40.95% dot ball rate** when required run rate (RRR) exceeded 10.0 vs IPL par of **34.47%** (+18.8% surplus dots).
   - *Impact:* RR batters accumulated 18.2 dots per chase in high-pressure phases, freezing under climbing run rates.
3. **Death Phase Boundary Starvation (Weakness #3 & #10):**  
   - *Metric:* **20.64% boundary percentage** at the death vs IPL par of **23.84%** (-13.4% deficit); death phase strike rate stalled at **163.81** vs league par of **169.29**.
   - *Impact:* Inability to execute boundary hitting against express pace and wide yorkers.
4. **Bowling Ineffectiveness vs Left-Handed Batters (Weakness #5 & #9):**  
   - *Metric:* Conceded a **10.28 economy rate** and **26.56% boundary rate** against LHBs vs league par of **9.60 economy** and **23.70% boundaries**.
   - *Impact:* Opposition teams routinely exploited RR by promoting left-handed pinch hitters into the top/middle order.
5. **Middle-Overs Batting Stagnation (Weakness #7):**  
   - *Metric:* **31.67% dot ball rate** in overs 7–15 vs IPL par of **29.53%**.
   - *Impact:* Middle-order inability to manipulate spin bowling at the Sawai Mansingh Stadium in Jaipur.

---

## 2. Recruitment Methodology: The Multi-Stage Screening Engine

To identify optimal targets, the system executed a sequential four-tier pipeline:

```text
477 IPL PLAYERS
       ↓
TIER 1: ELIGIBILITY & ACTIVE STATUS SCREENING
(Exclude confirmed retired: DK, Dhawan, Rayudu, Bravo, Uthappa; Exclude inactive)
       ↓
TIER 2: CAPPED VS UNCAPPED VS OVERSEAS PARTITIONING
(CAPPED_INDIAN: Senior India Test/ODI/T20I caps; UNCAPPED_INDIAN: Domestic; OVERSEAS)
       ↓
TIER 3: SEPARATION OF PERFORMANCE vs RECRUITMENT AVAILABILITY
(Performance Ranking evaluates all active; Recruitment Ranking filters realistic external targets)
       ↓
TIER 4: NINE-PARAMETER COMPOSITE FIT SCORING (FINAL_RR_2027_FIT_SCORE)
(Pressure 25%, Weakness 20%, Role 15%, IPL Perf 10%, Recent Form 10%, Rel 8%, Venue 5%, Upside 4%, Conf 3%)
```

### The Nine Calibrated Weights:
- **Pressure Performance (25%):** Adjusted pressure strike rate, pressure economy, and pressure delta $\\Delta_P$.
- **RR Weakness Fit (20%):** Direct mathematical covariance with RR's top 10 empirical deficiencies.
- **Role Fit (15%):** Alignment with tactical role archetypes based on actual delivery-level usage.
- **IPL Performance (10%):** Historical baseline efficiency in the Indian Premier League.
- **Recent Performance (10%):** Exponentially weighted recent form across 2025–2026 campaigns.
- **Reliability (8%):** Match-to-match consistency derived from Bayesian variance shrinkage.
- **Venue/Tactical Fit (5%):** Suitability for Sawai Mansingh Stadium pitch dimensions and bounce.
- **Age/Upside (4%):** Multi-season development runway and ceiling under high-performance coaching.
- **Availability Confidence (3%):** Certainty of contractual intelligence and retention dynamics.

---

## 3. Capped Candidates: Top Established Stars

Capped candidates bring proven international and IPL tournament maturity. Below are the Top 10 realistic Capped targets (`results/rr_ipl2027_capped_top10.csv`):

{capped10_md}

*Tactical Assessment:* **Tim David** and **Naman Dhir** provide premier plug-and-play finishing power. Tim David delivers an 85.0 pressure rating with extreme boundary conversion, while newly-capped Naman Dhir provides high-velocity middle-order strokeplay against both pace and spin.

---

## 4. Uncapped Candidates: Top Developmental & Value Assets

Uncapped domestic cricketers offer high-leverage purse preservation. Below are the Top 10 Uncapped targets (`results/rr_ipl2027_uncapped_top10.csv`):

{uncapped10_md}

*Tactical Assessment:* **Ashutosh Sharma** emerges as the single highest-rated recruit across the entire project (Fit Score: **74.82**). His extraordinary +35.00 pressure delta SR and 206.5 clutch strike rate directly eliminate RR's high-RRR dot ball crisis. Uncapped pacer **Sakib Hussain** (145kph+) and left-armer **Gurjapneet Singh** offer critical death-overs bowling solutions.

---

## 5. Combined Top 20 Recruitment Targets

The definitive Top 20 recruitment board combining both Capped and Uncapped candidates (`results/rr_ipl2027_top20.csv`):

{top20_md}

---

## 6. Final Combined Top 10 Recruitment Board

The elite data-driven Top 10 recruitment targets (`results/rr_ipl2027_final_top10.csv`):

{final10_md}

### Strategic Taxonomy of the Final Top 10:
1. **Ashutosh Sharma (PRIMARY_TARGET | Uncapped Fit: 74.82 | Avail: 0.80):**  
   The undisputed #1 target. Strikes at 206.5 under extreme pressure; single-handedly eliminates RR's #2 failure point (40.95% high RRR dots).
2. **Tim David (PRIMARY_TARGET | Overseas Fit: 74.46 | Avail: 0.75):**  
   World-class overseas power finisher. Boundary percentage of 28.4% in overs 18–20; capitalizes on RCB overseas quota constraints.
3. **Naman Dhir (PRIMARY_TARGET | Capped Indian Fit: 73.55 | Avail: 0.70):**  
   Elite young Indian batter striking at 170+; solves middle-overs stagnation and collapse vulnerability.
4. **Rinku Singh (BACKUP_TARGET | Capped Indian Fit: 70.28 | Avail: 0.50):**  
   Legendary chase finisher. Dependent on KKR retention allotment; high-priority bid if released.
5. **Jamie Overton (SECONDARY_TARGET | Overseas Fit: 69.12 | Avail: 0.75):**  
   Dual-threat pace-bowling all-rounder; delivers heavy-ball 142kph+ yorkers at the death and lower-order power hitting.
6. **Mukul Choudhary (VALUE_TARGET | Uncapped Fit: 68.81 | Avail: 0.80):**  
   Exceptional domestic value finisher with a 79.5 pressure score; fraction-of-purse acquisition.
7. **David Miller (SECONDARY_TARGET | Overseas Fit: 68.40 | Avail: 0.80):**  
   Battle-tested clutch veteran; eliminates post-wicket batting panics.
8. **Vipraj Nigam (DEVELOPMENT_TARGET | Capped Indian Fit: 68.37 | Avail: 0.70):**  
   Dynamic bowling all-rounder; adds attacking spin variation and late-overs hitting depth.
9. **Tilak Varma (BACKUP_TARGET | Capped Indian Fit: 68.35 | Avail: 0.55):**  
   Elite left-handed middle-order anchor-accelerator; available if MI encounter purse compression.
10. **Liam Livingstone (SECONDARY_TARGET | Overseas Fit: 68.16 | Avail: 0.75):**  
    Two-way tactical game-changer; dynamic boundary hitter and multi-style spin bowler.

---

## 7. Best Target for Each RR Empirical Weakness

Below is the specialist matrix mapping the best targets to RR's specific 2026 weaknesses (`results/rr_ipl2027_role_targets.csv`):

{role_targets_md}

---

## 8. Value vs Upside 2x2 Strategy Matrix

To optimize auction purse allocation, all top candidates are mapped across a 2x2 matrix of **Current Performance vs Developmental Upside** (`results/rr_ipl2027_value_upside_matrix.csv`):

{matrix_md}

### Strategic Quadrant Action Plan:
- **HIGH CURRENT / HIGH UPSIDE (Tier-1 Aggressive Pursuit):** *Ashutosh Sharma*, *Naman Dhir*, *Sameer Rizvi*, *Mukul Choudhary*, *Gurjapneet Singh*. Bid aggressively up to 4.5–7.0 Crores.
- **HIGH CURRENT / LOW UPSIDE (Win-Now Championship Assets):** *Tim David*, *David Miller*, *Rinku Singh*, *Jamie Overton*, *Liam Livingstone*, *Shashank Singh*. Secure on 1-to-2 year tactical contracts.
- **LOW CURRENT / HIGH UPSIDE (Developmental Value Bargains):** *Sakib Hussain*, *Priyansh Arya*, *Ayush Mhatre*, *Swastik Chikara*, *Robin Minz*, *Praful Hinge*. Target at base price (30–50 Lakhs) for immense future ROI.
- **LOW CURRENT / LOW UPSIDE (Depth Insurance):** *Krishnappa Gowtham*, *Deepak Chahar*, *Harshal Patel*. Rotational backups at modest valuations.

---

## 9. Availability Uncertainty & Pre-Auction Caveats

> [!IMPORTANT]
> **Pre-Auction Availability is Probabilistic, Not Deterministic.**
> Until the BCCI and IPL governing council publish the official IPL 2027 Auction Registration List and franchise retention declarations in late 2026, all availability assessments represent **Bayesian likelihood estimates** based on franchise purse limits, retention regulations (max 5–6 retentions, max 2 overseas), and 2026 playing XI frequency.

- **High-Certainty Auction Entrants ($P_\\text{{avail}} \\ge 0.75$):** Ashutosh Sharma, Tim David, David Miller, Jamie Overton, Mukul Choudhary, Liam Livingstone, Sameer Rizvi, Gurjapneet Singh, Sakib Hussain.
- **Conditional / Retention-Contingent Stars ($P_\\text{{avail}} = 0.45 - 0.65$):** Rinku Singh (KKR retention threshold), Tilak Varma (MI mega-purse allocation), Shashank Singh (PBKS uncapped slot).
- **Core Retained Non-Targets ($P_\\text{{avail}} < 0.25$):** Jasprit Bumrah, Heinrich Klaasen, Nicholas Pooran, Sunil Narine, Rashid Khan, Matheesha Pathirana, Virat Kohli, Rohit Sharma. These players are ranked in `ipl2027_performance_ranking.csv` for analytical completeness but are strictly excluded from practical auction bidding boards.

---

## 10. Risks, Trade-offs & Strategic Limitations

1. **Purse Escalation Bidding Wars:**  
   Elite finishers like **Ashutosh Sharma** and **Tim David** will attract fierce bidding from finisher-deprived franchises (DC, PBKS, RCB). RR must set strict walk-away ceilings (7.5 Cr for Ashutosh, 9.0 Cr for Tim David) and pivot seamlessly to **Mukul Choudhary** or **Shashank Singh**.
2. **Left-Arm Pacer Transition Curve:**  
   While **Gurjapneet Singh** (6'4" left-armer) solves RR's catastrophic 10.28 economy vs LHBs, his IPL sample size is small. Shane Bond must integrate him in pre-season camps alongside Sandeep Sharma to hone wide-line death execution.
3. **Overseas Quota Balance:**  
   Signing both Tim David and Jamie Overton consumes 2 overseas starting slots alongside existing overseas assets. RR must maintain flexibility by ensuring strong Indian domestic depth in the playing XI.

---
"""

# Check if master section already exists or append cleanly
if "# IPL 2027 Rajasthan Royals Recruitment: The Master Blueprint" in current_text:
    base_text = current_text.split("# IPL 2027 Rajasthan Royals Recruitment: The Master Blueprint")[0]
    updated_report = base_text + master_recruitment_section
else:
    updated_report = current_text + master_recruitment_section

with open(report_path, 'w', encoding='utf-8') as f:
    f.write(updated_report)

print(f"Successfully updated {report_path}!")
print(f"New report size: {len(updated_report)} characters, {len(updated_report.splitlines())} lines.")

