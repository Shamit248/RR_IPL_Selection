"""Quick audit of existing pipeline outputs"""
import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings('ignore')

OUT  = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\results'
DATA = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\6af3166e7b922_data_pack'

# ── 1. PRESSURE FEATURES ─────────────────────────────────────────────────────
print("=" * 60)
print("VALIDATING pressure_features.csv")
print("=" * 60)
pf = pd.read_csv(f'{OUT}/pressure_features.csv')
print(f"Rows: {len(pf):,}  Cols: {len(pf.columns)}")
print("Columns:", list(pf.columns))
print()

# Check pressure_index
if 'pressure_index' in pf.columns:
    print("pressure_index stats:")
    print(pf['pressure_index'].describe().round(3))
    print()

if 'pressure_category' in pf.columns:
    print("pressure_category counts:")
    print(pf['pressure_category'].value_counts().sort_index())
    print()

# Leakage check: first delivery of each innings should have score_before_ball=0
if 'score_before_ball' in pf.columns and 'innings_ball_num' in pf.columns:
    first_del = pf[pf['innings_ball_num'] == 1]
    smin = first_del['score_before_ball'].min()
    smax = first_del['score_before_ball'].max()
    print(f"Leakage check - score_before_ball at ball#1 (should all be 0): min={smin}, max={smax}")
    if smax == 0:
        print("  PASS: No score leakage detected")
    else:
        print("  FAIL: Score leakage detected!")
    print()

print("innings values:", sorted(pf['innings'].unique()))
if 'is_ipl' in pf.columns:
    print(f"is_ipl: {pf['is_ipl'].sum():,} True | {(~pf['is_ipl']).sum():,} False")
print()

key_cols = [
    'score_before_ball','wickets_lost_before_ball','wickets_remaining',
    'legal_ball_seq','balls_remaining','current_run_rate',
    'required_run_rate','runs_required','target',
    'runs_last_6_balls','runs_last_12_balls','wickets_last_6_balls',
    'boundaries_last_6_balls','partnership_runs','partnership_balls',
    'previous_over_runs','previous_over_wickets',
    'innings_phase','P1','P2','P3','P4','P5','P6',
    'pressure_index','pressure_category',
    'is_ipl','is_t20i','season','team_runs_ball','is_legal'
]
print("Key column presence:")
for c in key_cols:
    if c in pf.columns:
        nn  = pf[c].notna().sum()
        pct = nn / len(pf) * 100
        print(f"  [OK] {c:35s}: {nn:>8,} non-null ({pct:.1f}%)")
    else:
        print(f"  [MISSING] {c}")

# ── 2. MATCH STATE FEATURES ───────────────────────────────────────────────────
print()
print("=" * 60)
print("VALIDATING match_state_features.csv")
print("=" * 60)
ms = pd.read_csv(f'{OUT}/match_state_features.csv', nrows=5)
print("Columns:", list(ms.columns))

# ── 3. PLAYER METRICS - check what exists ─────────────────────────────────────
print()
print("=" * 60)
print("MISSING RESULTS CHECK")
print("=" * 60)
expected = [
    'player_batting_metrics.csv',
    'player_bowling_metrics.csv',
    'pressure_player_metrics.csv',
    'player_reliability.csv',
    'player_role_analysis.csv',
    'rr_batting_analysis.csv',
    'rr_bowling_analysis.csv',
    'rr_weaknesses.csv',
    'rr_required_player_profiles.csv',
    'model_validation.csv',
    'model_comparison.csv',
    'player_fit_scores.csv',
    'young_uncapped_targets.csv',
    'rr_ipl2027_rankings.csv',
    'final_report.md',
]
for f in expected:
    path = f'{OUT}/{f}'
    if os.path.exists(path):
        sz = os.path.getsize(path)
        print(f"  [EXISTS]  {f} ({sz/1024:.0f} KB)")
    else:
        print(f"  [MISSING] {f}")

# ── 4. CHECK EXISTING SCRIPTS ─────────────────────────────────────────────────
print()
print("=" * 60)
print("EXISTING SCRIPTS")
print("=" * 60)
base = r'C:\Users\LOQ\Desktop\RR_IPL_Selection'
for f in sorted(os.listdir(base)):
    if f.endswith('.py'):
        sz = os.path.getsize(f'{base}/{f}')
        print(f"  {f}: {sz/1024:.0f} KB")

# ── 5. SAMPLE PRESSURE DATA SANITY ───────────────────────────────────────────
print()
print("=" * 60)
print("PRESSURE SANITY — BATTING SR BY PRESSURE CATEGORY (IPL)")
print("=" * 60)
if 'is_ipl' in pf.columns and 'pressure_category' in pf.columns and 'is_legal' in pf.columns:
    ipl_legal = pf[(pf['is_ipl']) & (pf['is_legal'] == True)]
    sr_tab = ipl_legal.groupby('pressure_category').agg(
        balls=('runs', 'count'),
        runs=('runs', 'sum'),
        wickets=('is_wicket', 'sum')
    ).reset_index()
    sr_tab['SR'] = (sr_tab['runs'] / sr_tab['balls'] * 100).round(2)
    sr_tab['W_per_100'] = (sr_tab['wickets'] / sr_tab['balls'] * 100).round(3)
    sr_tab['pct'] = (sr_tab['balls'] / sr_tab['balls'].sum() * 100).round(1)
    print(sr_tab[['pressure_category','balls','SR','W_per_100','pct']].to_string(index=False))
else:
    print("  Missing required columns for sanity check")

