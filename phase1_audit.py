"""
PHASE 1 — FULL DATA AUDIT
RR IPL 2027 Recruitment Intelligence System
"""
import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings('ignore')

DATA = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\6af3166e7b922_data_pack'
OUT  = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\results'
os.makedirs(OUT, exist_ok=True)

# ── LOAD ──────────────────────────────────────────────────────────────────────
print("Loading datasets...")
comp  = pd.read_csv(f'{DATA}/competitions.csv')
teams = pd.read_csv(f'{DATA}/teams.csv')
mat   = pd.read_csv(f'{DATA}/matches.csv')
bbb   = pd.read_csv(f'{DATA}/ball_by_ball.csv')
pe    = pd.read_csv(f'{DATA}/playing_eleven.csv')
cmap  = pd.read_csv(f'{DATA}/competition_team_player_mapping.csv')
mat['match_date'] = pd.to_datetime(mat['match_date'])
print("Loaded.\n")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — DATASET SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("SECTION 1: DATASET SUMMARY")
print("=" * 70)

rows = []
for name, df, id_col, date_col in [
    ('competitions', comp, 'comp_id', None),
    ('teams',        teams, 'team_id', None),
    ('matches',      mat,  'match_id', 'match_date'),
    ('playing_eleven', pe, 'player_id', None),
    ('comp_map',     cmap, 'player_id', None),
    ('ball_by_ball', bbb,  'match_id', None),
]:
    total_null = df.isnull().sum().sum()
    null_pct   = round(100 * total_null / (df.shape[0] * df.shape[1]), 2)
    dups       = df.duplicated().sum()
    date_range = ''
    if date_col and date_col in df.columns:
        date_range = f"{df[date_col].min().date()} to {df[date_col].max().date()}"

    r = {
        'dataset':       name,
        'rows':          len(df),
        'columns':       len(df.columns),
        'unique_id':     df[id_col].nunique() if id_col in df.columns else 'N/A',
        'null_cells':    total_null,
        'null_pct':      null_pct,
        'duplicates':    dups,
        'date_range':    date_range,
    }
    rows.append(r)
    print(f"  {name:30s}: {len(df):>8,} rows | {len(df.columns):>3} cols | "
          f"nulls={total_null:,} ({null_pct}%) | dups={dups}")

summary_df = pd.DataFrame(rows)
summary_df.to_csv(f'{OUT}/dataset_summary.csv', index=False)
print(f"\n  → saved: {OUT}/dataset_summary.csv\n")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — COMPETITION AUDIT
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("SECTION 2: COMPETITION AUDIT")
print("=" * 70)

print("\nAll match_format values:")
print(comp['match_format'].value_counts().to_string())

print("\nAll seasons:")
print(comp['season'].value_counts().sort_index().to_string())

# IPL
ipl = comp[comp['comp_name'].str.contains('IPL|Indian Premier League', case=False, na=False)].copy()
print(f"\nIPL competitions found: {len(ipl)}")
print(ipl[['comp_id','comp_name','match_format','season']].to_string())

# T20I
t20i = comp[comp['match_format'].str.upper() == 'T20I'].copy()
print(f"\nT20I competitions found: {len(t20i)}")

# Match counts per competition
match_counts = mat['comp_id'].value_counts().reset_index()
match_counts.columns = ['comp_id','match_count']

comp_audit = comp.merge(match_counts, on='comp_id', how='left')
comp_audit['match_count'] = comp_audit['match_count'].fillna(0).astype(int)
comp_audit.to_csv(f'{OUT}/competition_audit.csv', index=False)
print(f"\n  → saved: {OUT}/competition_audit.csv")

print("\nIPL with match counts:")
ipl_audit = comp_audit[comp_audit['comp_id'].isin(ipl['comp_id'])]
print(ipl_audit[['comp_id','comp_name','season','match_count']].to_string())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — RELATIONSHIP VALIDATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 3: RELATIONSHIP VALIDATION")
print("=" * 70)

checks = {
    'matches -> competitions':     len(mat[~mat['comp_id'].isin(comp['comp_id'])]),
    'ball_by_ball -> matches':     len(bbb[~bbb['match_id'].isin(mat['match_id'])]),
    'playing_eleven -> matches':   len(pe[~pe['match_id'].isin(mat['match_id'])]),
    'teams -> competitions':       len(teams[~teams['comp_id'].isin(comp['comp_id'])]),
    'comp_map -> competitions':    len(cmap[~cmap['comp_id'].isin(comp['comp_id'])]),
}
for rel, orphans in checks.items():
    status = "✓ OK" if orphans == 0 else f"⚠ {orphans:,} ORPHAN ROWS"
    print(f"  {rel:40s}: {status}")

# How many match_ids in bbb have no playing_eleven record?
bbb_matches = set(bbb['match_id'].unique())
pe_matches  = set(pe['match_id'].unique())
print(f"\n  bbb match_ids not in playing_eleven : {len(bbb_matches - pe_matches)}")
print(f"  playing_eleven match_ids not in bbb  : {len(pe_matches - bbb_matches)}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — IPL + T20I IDENTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 4: IPL & T20I IDENTIFICATION")
print("=" * 70)

ipl_comp_ids  = set(ipl['comp_id'])
t20i_comp_ids = set(t20i['comp_id'])

ipl_matches  = mat[mat['comp_id'].isin(ipl_comp_ids)].copy()
t20i_matches = mat[mat['comp_id'].isin(t20i_comp_ids)].copy()

print(f"  IPL  matches : {len(ipl_matches):>5,}")
print(f"  T20I matches : {len(t20i_matches):>5,}")
print(f"  IPL  deliveries : {len(bbb[bbb['match_id'].isin(ipl_matches['match_id'])]):>8,}")
print(f"  T20I deliveries : {len(bbb[bbb['match_id'].isin(t20i_matches['match_id'])]):>8,}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — RAJASTHAN ROYALS IDENTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 5: RAJASTHAN ROYALS IDENTIFICATION")
print("=" * 70)

rr_teams = teams[teams['team_name'].str.contains('Rajasthan', case=False, na=False)]
print("Teams matching 'Rajasthan':")
print(rr_teams.to_string())

rr_team_ids = set(rr_teams['team_id'].unique())
print(f"\nRR team_id(s): {rr_team_ids}")

# Also check in cmap
rr_cmap = cmap[cmap['team_name'].str.contains('Rajasthan', case=False, na=False)]
print(f"\nRR entries in comp_map: {len(rr_cmap)}")
print(rr_cmap[['comp_id','comp_name','team_id','team_name']].drop_duplicates().to_string())

# Verify which IPL competitions RR participated in
rr_ipl_comps = rr_teams[rr_teams['comp_id'].isin(ipl_comp_ids)]
print("\nRR in IPL competitions:")
rr_ipl_comp_detail = rr_ipl_comps.merge(ipl[['comp_id','comp_name','season']], on='comp_id', how='left')
print(rr_ipl_comp_detail.to_string())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — RR IPL 2026 MATCHES
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 6: RR IPL 2026 MATCHES")
print("=" * 70)

# Find IPL 2026 competition
ipl_2026 = ipl[ipl['season'].astype(str) == '2026']
print(f"IPL 2026 comp(s): {ipl_2026[['comp_id','comp_name','season']].values}")

ipl_2026_comp_ids = set(ipl_2026['comp_id'])
ipl_2026_matches  = mat[mat['comp_id'].isin(ipl_2026_comp_ids)].copy()
print(f"Total IPL 2026 matches: {len(ipl_2026_matches)}")

# RR matches = where home or away team is RR
rr_ipl_2026 = ipl_2026_matches[
    ipl_2026_matches['home_team_id'].isin(rr_team_ids) |
    ipl_2026_matches['away_team_id'].isin(rr_team_ids)
].copy()

print(f"RR IPL 2026 matches: {len(rr_ipl_2026)}")
if len(rr_ipl_2026) > 0:
    print(rr_ipl_2026[['match_id','match_date','home_team','away_team','result']].to_string())
    rr_ipl_2026.to_csv(f'{OUT}/rr_ipl_2026_matches.csv', index=False)
    print(f"\n  → saved: {OUT}/rr_ipl_2026_matches.csv")
else:
    print("  ⚠ No RR IPL 2026 matches found — check IPL 2026 season label in competitions.csv")
    # Fallback: show all IPL seasons available
    print("\n  Available IPL seasons:")
    print(ipl[['comp_id','comp_name','season']].to_string())

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — RUNS / EXTRAS VALIDATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 7: RUNS & EXTRAS SANITY CHECK")
print("=" * 70)

print(f"  runs distribution (0–6):")
print(f"    {bbb['runs'].value_counts().sort_index().to_dict()}")
print(f"  Max runs on a delivery: {bbb['runs'].max()}")
print(f"  Runs > 6 (suspicious) : {(bbb['runs'] > 6).sum()}")
print(f"\n  extras1_runs > 0  : {(bbb['extras1_runs'] > 0).sum():>7,}")
print(f"  extras_2_runs > 0 : {(bbb['extras_2_runs'] > 0).sum():>7,}")
print(f"  Both extras > 0   : {((bbb['extras1_runs'] > 0) & (bbb['extras_2_runs'] > 0)).sum():>7,}")

print(f"\n  extras_type value counts:")
print(bbb['extras_type'].value_counts(dropna=False).head(10).to_string())

# When is_four=True, runs must be 4
four_runs = bbb[bbb['is_four']==True]['runs'].value_counts()
six_runs  = bbb[bbb['is_six']==True]['runs'].value_counts()
print(f"\n  runs when is_four=True  : {four_runs.to_dict()}")
print(f"  runs when is_six=True   : {six_runs.to_dict()}")

# Check for double-counting (runs includes extras or not?)
# If runs = 1 and extras1_runs = 1 → runs already includes extra
sample_extra = bbb[(bbb['extras1_runs'] > 0)][['runs','extras1_runs','extras_2_runs','extras_type']].head(20)
print(f"\n  Sample extra deliveries:")
print(sample_extra.to_string())

# When no extra, is runs the batsman's runs?
no_extra = bbb[bbb['extras1_runs'] == 0]
print(f"\n  runs distribution when extras1_runs=0:")
print(f"    {no_extra['runs'].value_counts().sort_index().head(8).to_dict()}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — MATCH STATE FEASIBILITY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 8: MATCH STATE FEASIBILITY CHECK")
print("=" * 70)

# Check overid and over_ball_num
print(f"  overid range       : {bbb['overid'].min()} to {bbb['overid'].max()}")
print(f"  over_ball_num range: {bbb['over_ball_num'].min()} to {bbb['over_ball_num'].max()}")
print(f"  innings values     : {sorted(bbb['innings'].unique())}")

# How many deliveries per over (should be ~6, may be more for wides/no-balls)
over_ball_counts = bbb.groupby(['match_id','innings','overid'])['over_ball_num'].count()
print(f"\n  Deliveries per over (distribution):")
print(f"    {over_ball_counts.value_counts().sort_index().head(10).to_dict()}")

# Verify innings_ball_num is monotonically increasing
test_match = bbb[bbb['match_id'] == bbb['match_id'].iloc[0]].copy()
test_inn = test_match[test_match['innings'] == 1]['innings_ball_num']
is_mono = (test_inn.diff().dropna() >= 0).all()
print(f"\n  innings_ball_num monotonically increasing (sample): {is_mono}")

# Check if revised matches exist
rev = mat[(mat['first_inn_revised_overs'].notna()) | (mat['second_inn_revised_overs'].notna())]
print(f"\n  Matches with revised overs: {len(rev)}")
print(f"  Matches with revised target: {mat['revised_target'].notna().sum()}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — MISSING DATA ISSUES
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 9: DATA QUALITY ISSUES SUMMARY")
print("=" * 70)

issues = []

# playing_eleven: 8667 null for is_captain, is_wk
pe_null_cap = pe['is_captain'].isnull().sum()
pe_null_wk  = pe['is_wk'].isnull().sum()
issues.append(f"playing_eleven.is_captain: {pe_null_cap:,} nulls ({100*pe_null_cap/len(pe):.1f}%) — may limit captain analysis")
issues.append(f"playing_eleven.is_wk:      {pe_null_wk:,} nulls ({100*pe_null_wk/len(pe):.1f}%) — WK identification partial")
issues.append(f"playing_eleven.batting_order: {pe['batting_order'].isnull().sum():,} nulls — some entries lack batting order")

# matches captain nulls
issues.append(f"matches.home_team_captain_id: {mat['home_team_captain_id'].isnull().sum()} nulls")
issues.append(f"matches.toss_win_team_id: {mat['toss_win_team_id'].isnull().sum()} nulls — toss data missing for {mat['toss_win_team_id'].isnull().sum()} matches")
issues.append(f"matches.win_team_id: {mat['win_team_id'].isnull().sum()} nulls — {mat['win_team_id'].isnull().sum()} matches with no winner (ties/no-result)")

# bbb
bbb_no_stroke = bbb['stroke'].isnull().sum()
issues.append(f"ball_by_ball.stroke: {bbb_no_stroke:,} nulls ({100*bbb_no_stroke/len(bbb):.1f}%) — shot type incomplete")
issues.append(f"ball_by_ball.bowl_speed: {(bbb['bowl_speed']==0).sum():,} zeros — speed data may be missing")

for i, issue in enumerate(issues, 1):
    print(f"  [{i:02d}] {issue}")

print("\n" + "=" * 70)
print("PHASE 1 AUDIT COMPLETE")
print("=" * 70)
print(f"Output files saved to: {OUT}")




