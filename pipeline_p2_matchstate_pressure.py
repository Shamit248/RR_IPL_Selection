"""
RR IPL 2027 Selection Pipeline — Phases 2–7
============================================
Match State Reconstruction, Innings Phase Classification,
Pressure Index Computation, and Pressure Category Assignment.

Data facts validated in Phase 1 audit:
  - extras1_runs is a ball-identifier field (equals ~6 on every row). IGNORED.
  - extras_2_runs is actual extras (non-zero on only 36 rows).
  - Super overs are innings 3/4 — filtered out.
  - overid is 1-indexed (1–20); converted to 0-indexed for phase logic.
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DATA_DIR = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\6af3166e7b922_data_pack'
OUT_DIR  = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\results'

IPL_COMP_IDS = {1358, 1715, 2193, 2725, 3298}   # 2022–2026 seasons
RR_TEAM_ID   = 3

# Weighting configs for Pressure Index sensitivity analysis
WEIGHT_CONFIGS = {
    'config_A': [0.30, 0.20, 0.20, 0.10, 0.10, 0.10],  # default (balanced)
    'config_B': [0.35, 0.15, 0.20, 0.10, 0.10, 0.10],  # RRR-focused
    'config_C': [0.25, 0.20, 0.25, 0.10, 0.10, 0.10],  # wickets-focused
}

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# SECTION 1 — LOAD & CLEAN
# ---------------------------------------------------------------------------
print("=" * 70)
print("SECTION 1 — Loading and cleaning data")
print("=" * 70)

print("  Loading ball_by_ball.csv ...")
bbb = pd.read_csv(os.path.join(DATA_DIR, 'ball_by_ball.csv'), low_memory=False)
print(f"    Raw ball_by_ball rows: {len(bbb):,}")

print("  Loading matches.csv ...")
matches = pd.read_csv(os.path.join(DATA_DIR, 'matches.csv'), low_memory=False)
print(f"    Raw matches rows: {len(matches):,}")

print("  Loading competitions.csv ...")
comps = pd.read_csv(os.path.join(DATA_DIR, 'competitions.csv'), low_memory=False)
print(f"    Raw competitions rows: {len(comps):,}")

# --- Filter out Super Overs (innings 3 and 4) ---
bbb = bbb[bbb['innings'].isin([1, 2])].copy()
print(f"    After filtering Super Overs (keep innings 1 & 2): {len(bbb):,} rows")

# --- Runs accounting ---
# CRITICAL: extras1_runs is NOT actual extras — IGNORE it completely.
# team_runs_ball = batter runs (runs) + actual extras (extras_2_runs)
bbb['extras_2_runs'] = pd.to_numeric(bbb['extras_2_runs'], errors='coerce').fillna(0)
bbb['runs']          = pd.to_numeric(bbb['runs'],          errors='coerce').fillna(0)
bbb['team_runs_ball'] = bbb['runs'] + bbb['extras_2_runs']

# --- Legal delivery flag ---
# A delivery is legal if extras_type is NOT 'wide' or 'Overstep' (no-ball)
bbb['is_legal'] = (
    bbb['extras_type'].isna() |
    ~bbb['extras_type'].isin(['wide', 'Overstep'])
).astype(int)

# --- Boolean helpers ---
bbb['is_wicket'] = pd.to_numeric(bbb['is_wicket'], errors='coerce').fillna(0).astype(int)
bbb['is_four']   = pd.to_numeric(bbb['is_four'],   errors='coerce').fillna(0).astype(int)
bbb['is_six']    = pd.to_numeric(bbb['is_six'],    errors='coerce').fillna(0).astype(int)
bbb['is_boundary'] = ((bbb['is_four'] == 1) | (bbb['is_six'] == 1)).astype(int)

# --- Merge match metadata ---
# Columns needed from matches
match_meta_cols = [
    'match_id', 'match_date', 'comp_id', 'venue_id', 'stage',
    'home_team_id', 'away_team_id',
    'first_inn_revised_overs', 'second_inn_revised_overs',
    'revised_target', 'win_team_id', 'knock_out'
]
# Keep only columns that actually exist in matches.csv
avail_meta = [c for c in match_meta_cols if c in matches.columns]
matches_sub = matches[avail_meta].drop_duplicates(subset=['match_id'])

bbb = bbb.merge(matches_sub, on='match_id', how='left', suffixes=('', '_meta'))
print(f"    After merging match metadata: {len(bbb):,} rows")

# --- Flags: IPL and T20I ---
bbb['is_ipl'] = bbb['comp_id'].isin(IPL_COMP_IDS).astype(int)
# T20I competitions are identified by competition type; use a reasonable heuristic
# (competitions table has a 'type' or 'comp_type' column if it exists)
t20i_comp_ids = set()
if 'comp_type' in comps.columns:
    t20i_comp_ids = set(comps.loc[comps['comp_type'].str.lower().str.contains('t20i', na=False), 'comp_id'].tolist())
elif 'type' in comps.columns:
    t20i_comp_ids = set(comps.loc[comps['type'].str.lower().str.contains('t20i', na=False), 'comp_id'].tolist())
bbb['is_t20i'] = bbb['comp_id'].isin(t20i_comp_ids).astype(int)

# --- innings_ball_num as numeric for sorting ---
bbb['innings_ball_num'] = pd.to_numeric(bbb['innings_ball_num'], errors='coerce').fillna(0)
bbb['overid']           = pd.to_numeric(bbb['overid'],           errors='coerce').fillna(1)

print(f"  Section 1 complete. Working rows: {len(bbb):,}")

# ---------------------------------------------------------------------------
# SECTION 2 — SORT AND INDEX
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 2 — Sorting data")
print("=" * 70)

# Sort ensures cumulative operations are chronologically correct
bbb = bbb.sort_values(['match_id', 'innings', 'innings_ball_num']).reset_index(drop=True)
print(f"  Sorted by match_id, innings, innings_ball_num. Total rows: {len(bbb):,}")

# ---------------------------------------------------------------------------
# SECTION 3 — MATCH STATE RECONSTRUCTION
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 3 — Computing match state features (pre-delivery, no leakage)")
print("=" * 70)

grp_mi = bbb.groupby(['match_id', 'innings'], sort=False)

# --- Score and wickets before this delivery ---
print("  Computing score_before_ball and wickets_lost_before_ball ...")
bbb['score_before_ball'] = (
    grp_mi['team_runs_ball']
    .transform(lambda s: s.cumsum().shift(1).fillna(0))
)
bbb['wickets_lost_before_ball'] = (
    grp_mi['is_wicket']
    .transform(lambda s: s.cumsum().shift(1).fillna(0))
)
bbb['wickets_remaining'] = 10 - bbb['wickets_lost_before_ball']

# --- Legal ball sequence (for overs_completed calculation) ---
print("  Computing legal_ball_seq ...")
bbb['legal_ball_seq'] = (
    grp_mi['is_legal']
    .transform(lambda s: s.cumsum().shift(1).fillna(0))
)

# --- Max overs per innings (DL adjustments) ---
print("  Computing max_overs (with DL adjustment) ...")
# Default to 20 overs
bbb['max_overs'] = 20.0

# Apply first innings DL revision
if 'first_inn_revised_overs' in bbb.columns:
    mask1 = (bbb['innings'] == 1) & bbb['first_inn_revised_overs'].notna()
    bbb.loc[mask1, 'max_overs'] = pd.to_numeric(
        bbb.loc[mask1, 'first_inn_revised_overs'], errors='coerce'
    ).fillna(20)

# Apply second innings DL revision
if 'second_inn_revised_overs' in bbb.columns:
    mask2 = (bbb['innings'] == 2) & bbb['second_inn_revised_overs'].notna()
    bbb.loc[mask2, 'max_overs'] = pd.to_numeric(
        bbb.loc[mask2, 'second_inn_revised_overs'], errors='coerce'
    ).fillna(20)

bbb['balls_in_innings'] = bbb['max_overs'] * 6
bbb['balls_remaining']  = (bbb['balls_in_innings'] - bbb['legal_ball_seq']).clip(lower=0)

# --- Current Run Rate ---
print("  Computing current_run_rate ...")
bbb['overs_completed'] = bbb['legal_ball_seq'] / 6.0
# Avoid div-by-zero: CRR = 0 when no overs bowled yet
bbb['current_run_rate'] = np.where(
    bbb['overs_completed'] > 0,
    bbb['score_before_ball'] / bbb['overs_completed'],
    0.0
)

# --- Rolling windows: runs, wickets, boundaries (previous N deliveries) ---
print("  Computing rolling window features (last 6/12/18 balls) ...")

def rolling_shift(series, window):
    """Rolling sum of previous window deliveries (shift(1) ensures no leakage)."""
    return series.rolling(window=window, min_periods=1).sum().shift(1).fillna(0)

# Apply within each match-innings group
for col, alias in [
    ('team_runs_ball', 'runs'),
    ('is_wicket',      'wickets'),
    ('is_boundary',    'boundaries'),
]:
    for w in ([6, 12, 18] if alias == 'runs' else [6, 12]):
        out_col = f'{alias}_last_{w}_balls'
        bbb[out_col] = grp_mi[col].transform(lambda s, w=w: rolling_shift(s, w))

# --- Partnership tracking (reset on each wicket) ---
print("  Computing partnership features ...")
# wicket_number before this ball = cumsum of wickets before this delivery
# This uniquely identifies each partnership within an innings
bbb['wicket_number'] = bbb['wickets_lost_before_ball'].astype(int)

grp_part = bbb.groupby(['match_id', 'innings', 'wicket_number'], sort=False)
bbb['partnership_runs'] = (
    grp_part['team_runs_ball']
    .transform(lambda s: s.cumsum().shift(1).fillna(0))
)
bbb['partnership_balls'] = (
    grp_part['is_legal']
    .transform(lambda s: s.cumsum().shift(1).fillna(0))
)

# --- Previous over stats ---
print("  Computing previous_over_runs and previous_over_wickets ...")
bbb['over_0indexed'] = (bbb['overid'] - 1).astype(int)

# Aggregate by match_id, innings, over — sum runs and wickets in that over
over_agg = (
    bbb.groupby(['match_id', 'innings', 'over_0indexed'], sort=False)
    .agg(
        over_runs=('team_runs_ball', 'sum'),
        over_wickets=('is_wicket',   'sum'),
    )
    .reset_index()
)
# Lag: shift over stats by 1 within each match-innings
over_agg = over_agg.sort_values(['match_id', 'innings', 'over_0indexed'])
over_agg['previous_over_runs']    = (
    over_agg.groupby(['match_id', 'innings'])['over_runs']
    .transform(lambda s: s.shift(1).fillna(0))
)
over_agg['previous_over_wickets'] = (
    over_agg.groupby(['match_id', 'innings'])['over_wickets']
    .transform(lambda s: s.shift(1).fillna(0))
)
# Merge back (each ball in an over gets that over's previous-over values)
bbb = bbb.merge(
    over_agg[['match_id', 'innings', 'over_0indexed',
              'previous_over_runs', 'previous_over_wickets']],
    on=['match_id', 'innings', 'over_0indexed'],
    how='left'
)
bbb[['previous_over_runs', 'previous_over_wickets']] = (
    bbb[['previous_over_runs', 'previous_over_wickets']].fillna(0)
)

# --- Chase State (innings 2 only) ---
print("  Computing chase state (innings 2) ...")

# Step 1: Compute first-innings total for each match
# Sum all innings-1 team_runs_ball to get the total runs scored
inn1_totals = (
    bbb[bbb['innings'] == 1]
    .groupby('match_id')['team_runs_ball']
    .sum()
    .rename('inn1_total')
    .reset_index()
)
inn1_totals['inn1_target'] = inn1_totals['inn1_total'] + 1  # target = inn1 total + 1

# Step 2: Determine target for innings 2
# DL revised_target takes priority; fall back to inn1_target
bbb = bbb.merge(inn1_totals[['match_id', 'inn1_target']], on='match_id', how='left')

bbb['target'] = np.nan
mask_inn2 = bbb['innings'] == 2

# Use revised_target if available (DL matches)
if 'revised_target' in bbb.columns:
    bbb['revised_target'] = pd.to_numeric(bbb['revised_target'], errors='coerce')
    has_revised = mask_inn2 & bbb['revised_target'].notna()
    bbb.loc[has_revised, 'target'] = bbb.loc[has_revised, 'revised_target']

# Fall back to inn1_target where target not yet set
no_target = mask_inn2 & bbb['target'].isna()
bbb.loc[no_target, 'target'] = bbb.loc[no_target, 'inn1_target']

# Innings 1: target stays NaN (not applicable)
bbb['runs_required'] = np.where(
    mask_inn2,
    (bbb['target'] - bbb['score_before_ball']).clip(lower=0),
    np.nan
)

# Required Run Rate (RRR)
bbb['required_run_rate'] = np.where(
    mask_inn2 & (bbb['balls_remaining'] > 0),
    bbb['runs_required'] / (bbb['balls_remaining'] / 6.0),
    np.where(mask_inn2, 0.0, np.nan)
)
# Cap at infinity guard
bbb['required_run_rate'] = (
    bbb['required_run_rate'].replace([np.inf, -np.inf], 0).fillna(0)
)

print(f"  Section 3 complete. Total columns: {len(bbb.columns)}")

# ---------------------------------------------------------------------------
# SECTION 4 — INNINGS PHASE CLASSIFICATION
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 4 — Innings phase classification (DL-adjusted)")
print("=" * 70)

# Phase boundaries scaled proportionally for DL-affected matches
# pp_end    = last Powerplay over index (0-indexed)
# death_start = first Death over index (0-indexed)
bbb['pp_end']      = (bbb['max_overs'] * 5.0 / 20.0).round().clip(upper=5).astype(int)
bbb['death_start'] = np.maximum(
    bbb['pp_end'] + 1,
    (bbb['max_overs'] * 15.0 / 20.0).round().astype(int)
)

# Classify each delivery's innings phase
conditions = [
    bbb['over_0indexed'] <= bbb['pp_end'],
    bbb['over_0indexed'] >= bbb['death_start'],
]
choices = ['POWERPLAY', 'DEATH']
bbb['innings_phase'] = np.select(conditions, choices, default='MIDDLE')

phase_counts = bbb['innings_phase'].value_counts()
print(f"  Phase distribution:\n{phase_counts.to_string()}")

# ---------------------------------------------------------------------------
# SECTION 5 — PRESSURE INDEX
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 5 — Computing Pressure Index components")
print("=" * 70)

# Convenience aliases
score   = bbb['score_before_ball']
crr     = bbb['current_run_rate']
rrr     = bbb['required_run_rate']
wl      = bbb['wickets_lost_before_ball']
wr      = bbb['wickets_remaining']
br      = bbb['balls_remaining']
max_b   = bbb['balls_in_innings']
rr      = bbb['runs_required']
inn2    = (bbb['innings'] == 2)

# ---- P1: RRR / Projected Score Pressure (weight 0.30) ---- #
print("  P1: RRR / projected-score pressure ...")

# Innings 2: normalize RRR (<=6 → 0, >=18 → 1)
p1_inn2 = ((rrr - 6.0) / (18.0 - 6.0)).clip(0, 1)

# Innings 1: use projected score vs par
par_score = 160.0
projected_score = score + crr * (br / 6.0)
p1_inn1_raw = ((par_score - projected_score) / par_score * 1.5).clip(0, 1)
# Cap at 0.3 when wickets_remaining > 7 (early, losing isn't yet catastrophic)
p1_inn1 = np.where(wr > 7, np.minimum(p1_inn1_raw, 0.3), p1_inn1_raw)

P1 = np.where(inn2, p1_inn2, p1_inn1)
bbb['P1'] = P1

# ---- P2: Balls Remaining Pressure (weight 0.20) ---- #
print("  P2: Balls remaining pressure ...")
# As balls tick down, pressure rises
bbb['P2'] = (1.0 - br / max_b.replace(0, np.nan)).clip(0, 1).fillna(0)

# ---- P3: Wickets Pressure (weight 0.20) ---- #
print("  P3: Wickets lost pressure ...")
bbb['P3'] = (wl / 10.0).clip(0, 1)

# ---- P4: Match Closeness (weight 0.10) ---- #
print("  P4: Match closeness ...")

# Innings 2: peaks when runs_required ≈ balls_remaining (tight game)
denom_inn2 = (rr + br).clip(lower=1)
p4_inn2 = (1.0 - (rr - br).abs() / denom_inn2).clip(0, 1)

# Innings 1: proxy using wickets × phase factor
phase_factor_map = {'POWERPLAY': 0.4, 'MIDDLE': 0.7, 'DEATH': 1.0}
phase_factor = bbb['innings_phase'].map(phase_factor_map).fillna(0.7)
p4_inn1 = ((wl / 10.0) * phase_factor).clip(0, 1)

bbb['P4'] = np.where(inn2, p4_inn2.fillna(0), p4_inn1)

# ---- P5: Innings Phase Multiplier (weight 0.10) ---- #
print("  P5: Innings phase multiplier ...")
phase_p5_map = {'POWERPLAY': 0.3, 'MIDDLE': 0.6, 'DEATH': 1.0}
bbb['P5'] = bbb['innings_phase'].map(phase_p5_map).fillna(0.6)

# ---- P6: Recent Momentum (weight 0.10) ---- #
print("  P6: Recent momentum pressure ...")
w6 = bbb['wickets_last_6_balls']
r6 = bbb['runs_last_6_balls']
b6 = bbb['boundaries_last_6_balls']

# Sub-component: recent wicket cluster
recent_wicket_pressure = (w6 / 3.0).clip(0, 1)

# Sub-component: RRR acceleration in last 6 balls (innings 2 only, >6 balls left)
# prev_rrr = what RRR was 6 balls ago
prev_rrr = np.where(
    inn2 & (br > 6),
    (rr + r6) / np.maximum((br + 6) / 6.0, 0.1),
    0.0
)
rrr_increase = np.maximum(0.0, rrr.values - prev_rrr)
rrr_accel    = np.clip(rrr_increase / 3.0, 0, 1)
rrr_accel    = np.where(inn2 & (br > 6), rrr_accel, 0.0)

# Boundary drought component (fewer boundaries in last 6 → more pressure)
boundary_drought = (1.0 - b6 / 3.0).clip(0, 1)

bbb['P6'] = (
    0.5 * recent_wicket_pressure + 0.5 * rrr_accel + 0.3 * boundary_drought
).clip(0, 1)

# ---- Compute pressure index for each weighting config ---- #
print("  Computing pressure indices for all weight configs ...")
p_cols = ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']

for cfg_name, weights in WEIGHT_CONFIGS.items():
    bbb[f'pressure_{cfg_name}'] = 100.0 * sum(
        w * bbb[p] for w, p in zip(weights, p_cols)
    )

# ---- Select best config by SR separation (NORMAL vs EXTREME) ---- #
print("  Evaluating configs: SR separation NORMAL vs EXTREME ...")

# Compute SR = (runs / legal balls faced) * 100
# Use batter_runs (= 'runs' col) and is_legal for SR
bbb['batter_runs'] = bbb['runs']  # confirmed correct in Phase 1 audit

best_config  = None
best_sep     = -np.inf

for cfg_name in WEIGHT_CONFIGS:
    pi_col = f'pressure_{cfg_name}'
    # Assign temp categories
    cats = pd.cut(
        bbb[pi_col],
        bins=[-np.inf, 30, 50, 70, np.inf],
        labels=['NORMAL', 'MODERATE', 'HIGH', 'EXTREME']
    )
    # SR = (batter_runs / is_legal) * 100 at delivery level;
    # group by category, then SR = sum(runs)/sum(legal)*100
    bbb['_tmp_cat'] = cats
    sr_by_cat = (
        bbb.groupby('_tmp_cat', observed=True)[['batter_runs', 'is_legal']]
        .sum()
        .apply(lambda r: r['batter_runs'] / r['is_legal'] * 100
               if r['is_legal'] > 0 else np.nan, axis=1)
    )
    bbb.drop(columns=['_tmp_cat'], inplace=True)
    normal_sr  = sr_by_cat.get('NORMAL',  np.nan)
    extreme_sr = sr_by_cat.get('EXTREME', np.nan)
    separation = (normal_sr - extreme_sr) if (not np.isnan(normal_sr) and not np.isnan(extreme_sr)) else -np.inf
    print(f"    {cfg_name}: NORMAL SR={normal_sr:.1f}, EXTREME SR={extreme_sr:.1f}, sep={separation:.1f}")
    if separation > best_sep:
        best_sep    = separation
        best_config = cfg_name

print(f"  → Best config: {best_config} (separation={best_sep:.1f})")
bbb['pressure_index'] = bbb[f'pressure_{best_config}']

# ---------------------------------------------------------------------------
# SECTION 6 — PRESSURE CATEGORIES
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 6 — Pressure category assignment")
print("=" * 70)

bbb['pressure_category'] = pd.cut(
    bbb['pressure_index'],
    bins=[-np.inf, 30, 50, 70, np.inf],
    labels=['NORMAL', 'MODERATE', 'HIGH', 'EXTREME']
)

# Verify thresholds produce meaningful SR separation
print("  Validating threshold separation (SR per pressure category):")
_grp_val = bbb.groupby('pressure_category', observed=True)[['batter_runs', 'is_legal', 'innings']]
sr_validation = pd.DataFrame({
    'deliveries':  bbb.groupby('pressure_category', observed=True)['innings'].count(),
    'batter_runs': bbb.groupby('pressure_category', observed=True)['batter_runs'].sum(),
    'legal_balls': bbb.groupby('pressure_category', observed=True)['is_legal'].sum(),
}).assign(mean_SR=lambda d: d['batter_runs'] / d['legal_balls'] * 100).reset_index()
print(sr_validation.to_string(index=False))

# ---------------------------------------------------------------------------
# SECTION 7 — OUTPUT
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 7 — Saving outputs and printing summary statistics")
print("=" * 70)

# --- Define which columns belong to match state features ---
# Original columns that came from ball_by_ball.csv
orig_bbb_cols = [
    'match_id', 'innings', 'innings_ball_num', 'overid', 'ball_num',
    'batter_id', 'non_striker_id', 'bowler_id', 'batting_team_id',
    'bowling_team_id', 'runs', 'extras_2_runs', 'extras_type',
    'is_wicket', 'wicket_kind', 'player_out_id',
    'is_four', 'is_six',
    'batter_runs',
]
# Keep only columns that actually exist
orig_bbb_cols = [c for c in orig_bbb_cols if c in bbb.columns]

# Match metadata columns
meta_cols = [c for c in [
    'match_date', 'comp_id', 'venue_id', 'stage',
    'home_team_id', 'away_team_id',
    'first_inn_revised_overs', 'second_inn_revised_overs',
    'revised_target', 'win_team_id', 'knock_out',
    'is_ipl', 'is_t20i',
] if c in bbb.columns]

# Match state feature columns (computed in Section 3)
state_cols = [
    'team_runs_ball', 'is_legal', 'is_boundary',
    'score_before_ball', 'wickets_lost_before_ball', 'wickets_remaining',
    'legal_ball_seq', 'max_overs', 'balls_in_innings', 'balls_remaining',
    'overs_completed', 'current_run_rate',
    'runs_last_6_balls', 'runs_last_12_balls', 'runs_last_18_balls',
    'wickets_last_6_balls', 'wickets_last_12_balls',
    'boundaries_last_6_balls', 'boundaries_last_12_balls',
    'wicket_number', 'partnership_runs', 'partnership_balls',
    'over_0indexed', 'previous_over_runs', 'previous_over_wickets',
    'target', 'runs_required', 'required_run_rate',
    'inn1_target',
    'pp_end', 'death_start',
]
state_cols = [c for c in state_cols if c in bbb.columns]

# Phase column
phase_cols = ['innings_phase']

# --- Save match_state_features.csv ---
match_state_col_set = orig_bbb_cols + meta_cols + state_cols + phase_cols
match_state_col_set = list(dict.fromkeys(match_state_col_set))  # deduplicate, preserve order
match_state_col_set = [c for c in match_state_col_set if c in bbb.columns]

out_state_path = os.path.join(OUT_DIR, 'match_state_features.csv')
print(f"  Saving match_state_features.csv ({len(bbb):,} rows × {len(match_state_col_set)} cols) ...")
bbb[match_state_col_set].to_csv(out_state_path, index=False)
print(f"  → Saved: {out_state_path}")

# --- Save pressure_features.csv ---
pressure_specific_cols = (
    p_cols +
    [f'pressure_{c}' for c in WEIGHT_CONFIGS] +
    ['pressure_index', 'pressure_category']
)
pressure_specific_cols = [c for c in pressure_specific_cols if c in bbb.columns]

pressure_col_set = match_state_col_set + pressure_specific_cols
pressure_col_set = list(dict.fromkeys(pressure_col_set))

out_pressure_path = os.path.join(OUT_DIR, 'pressure_features.csv')
print(f"  Saving pressure_features.csv ({len(bbb):,} rows × {len(pressure_col_set)} cols) ...")
bbb[pressure_col_set].to_csv(out_pressure_path, index=False)
print(f"  → Saved: {out_pressure_path}")

# --- Summary statistics ---
print()
print("─" * 70)
print("SUMMARY STATISTICS")
print("─" * 70)

# 1. Delivery count by pressure_category
print("\n1. Delivery count by pressure_category:")
count_by_cat = bbb['pressure_category'].value_counts().sort_index()
print(count_by_cat.to_string())

# 2. Mean batting SR by pressure_category
print("\n2. Mean batting Strike Rate by pressure_category (runs per 100 legal balls):")
sr_by_cat = (
    bbb.groupby('pressure_category', observed=True)[['batter_runs', 'is_legal']]
    .sum()
    .apply(lambda r: r['batter_runs'] / r['is_legal'] * 100
           if r['is_legal'] > 0 else np.nan, axis=1)
    .rename('mean_SR')
)
print(sr_by_cat.to_string())

# 3. Mean economy (bowler view) by pressure_category
# Economy = runs conceded per over (from bowler's perspective = team_runs_ball per legal ball * 6)
print("\n3. Mean economy (bowler view) by pressure_category (runs per over):")
eco_by_cat = (
    bbb.groupby('pressure_category', observed=True)[['team_runs_ball', 'is_legal']]
    .sum()
    .apply(lambda r: r['team_runs_ball'] / r['is_legal'] * 6
           if r['is_legal'] > 0 else np.nan, axis=1)
    .rename('mean_economy')
)
print(eco_by_cat.to_string())

# 4. Quick data integrity checks
print()
print("─" * 70)
print("DATA INTEGRITY CHECKS")
print("─" * 70)
print(f"  Total deliveries processed : {len(bbb):,}")
print(f"  Innings 1 deliveries       : {(bbb['innings'] == 1).sum():,}")
print(f"  Innings 2 deliveries       : {(bbb['innings'] == 2).sum():,}")
print(f"  IPL deliveries             : {bbb['is_ipl'].sum():,}")
print(f"  Pressure index range       : [{bbb['pressure_index'].min():.2f}, {bbb['pressure_index'].max():.2f}]")
print(f"  Pressure index mean        : {bbb['pressure_index'].mean():.2f}")
print(f"  Best config selected       : {best_config}")
print(f"  NORMAL–EXTREME SR sep      : {best_sep:.1f} runs per 100 balls")
print()
print("Pipeline Phases 2–7 complete. ✓")
print("=" * 70)
