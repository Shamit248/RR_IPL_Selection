"""
FIX SCRIPT: Add missing player/matchup columns to pressure_features.csv

The existing pressure_features.csv is missing:
  - striker_id, striker_name
  - non_striker_name  
  - bowler_id (exists but as a col), bowler_name
  - batting_type, bowling_type
  - batting_order
  - pace_or_spin
  - bowl_speed, stroke, delivery_style, over_or_around, on_or_off
  - dismissal_type, dismissal_type_id, dismissed_player_id
  - season
  - over_ball_num (may be missing too)

These are all in ball_by_ball.csv. We merge them back using match_id + innings_ball_num.
"""
import pandas as pd
import numpy as np
import os
import time
import warnings
warnings.filterwarnings('ignore')

DATA = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\6af3166e7b922_data_pack'
OUT  = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\results'

t0 = time.time()
print("=" * 60)
print("FIX: Adding missing columns to pressure_features.csv")
print("=" * 60)

# ── Load existing pressure_features ──────────────────────────────────────────
print("\nLoading pressure_features.csv ...")
pf = pd.read_csv(f'{OUT}/pressure_features.csv', low_memory=False)
print(f"  Loaded: {len(pf):,} rows × {len(pf.columns)} cols")

# ── Load raw ball_by_ball for missing columns ─────────────────────────────────
print("Loading ball_by_ball.csv ...")
bbb = pd.read_csv(f'{DATA}/ball_by_ball.csv', low_memory=False)
print(f"  Loaded: {len(bbb):,} rows")

# Filter bbb to innings 1 & 2 only (same filter that was applied to pf)
bbb = bbb[bbb['innings'].isin([1, 2])].copy()
print(f"  After innings filter: {len(bbb):,} rows")

# Columns we need to bring in from bbb that are missing from pf
missing_from_pf = []
needed_cols = [
    'striker_id', 'striker_name',
    'non_striker_id', 'non_striker_name',
    'bowler_name',
    'batting_type', 'bowling_type',
    'batting_order',
    'pace_or_spin', 'bowl_speed',
    'stroke', 'delivery_style', 'over_or_around', 'on_or_off',
    'dismissal_type_id', 'dismissal_type', 'dismissed_player_id',
    'over_ball_num',
    'delivery_ist_time',
]

for c in needed_cols:
    if c not in pf.columns and c in bbb.columns:
        missing_from_pf.append(c)
    elif c not in pf.columns and c not in bbb.columns:
        print(f"  WARNING: {c} not in bbb either — skipping")

print(f"\nColumns to add: {missing_from_pf}")

# ── Add season from competitions ──────────────────────────────────────────────
comp = pd.read_csv(f'{DATA}/competitions.csv', low_memory=False)
comp['season'] = comp['season'].astype(str).str[:4]  # take first 4 chars = year
season_map = comp.set_index('comp_id')['season'].to_dict()
if 'season' not in pf.columns:
    pf['season'] = pf['comp_id'].map(season_map)
    print(f"  Added 'season' column. Values: {pf['season'].unique()[:8]}")
else:
    print("  'season' already present")

if not missing_from_pf:
    print("\nNo missing player columns! Checking if season was the only gap...")
    # Still need to verify it's correct
    pf.to_csv(f'{OUT}/pressure_features.csv', index=False)
    print(f"Saved updated pressure_features.csv with season col.")
    exit()

# ── Build join key: match_id + innings + innings_ball_num ─────────────────────
# Both pf and bbb have match_id, innings, innings_ball_num
print("\nBuilding merge key on match_id + innings + innings_ball_num ...")

# Check bbb has innings_ball_num
assert 'innings_ball_num' in bbb.columns, "innings_ball_num missing from bbb!"
assert 'innings_ball_num' in pf.columns, "innings_ball_num missing from pf!"

# Select only needed cols from bbb for the merge (avoid column collisions)
# Keep key cols + the missing ones
merge_cols = ['match_id', 'innings', 'innings_ball_num'] + missing_from_pf
# Some of these may already exist in pf under same name
merge_cols = ['match_id', 'innings', 'innings_ball_num'] + [
    c for c in missing_from_pf if c not in pf.columns
]
bbb_slim = bbb[merge_cols].drop_duplicates(subset=['match_id','innings','innings_ball_num'])

print(f"  bbb_slim: {len(bbb_slim):,} rows")
print(f"  pf rows:  {len(pf):,}")

# Check for key uniqueness
dup_bbb = bbb_slim.duplicated(subset=['match_id','innings','innings_ball_num']).sum()
dup_pf  = pf.duplicated(subset=['match_id','innings','innings_ball_num']).sum()
print(f"  Duplicate keys in bbb_slim: {dup_bbb}")
print(f"  Duplicate keys in pf:       {dup_pf}")

# ── Merge ─────────────────────────────────────────────────────────────────────
print("\nMerging missing columns into pressure_features ...")
pf_merged = pf.merge(bbb_slim, on=['match_id','innings','innings_ball_num'], how='left')

# Verify row count preserved
assert len(pf_merged) == len(pf), f"Row count changed! {len(pf_merged)} vs {len(pf)}"
print(f"  Merge successful. Row count preserved: {len(pf_merged):,}")

# Check null rates in added columns
for c in missing_from_pf:
    if c in pf_merged.columns:
        null_count = pf_merged[c].isna().sum()
        print(f"  {c}: {null_count:,} nulls ({null_count/len(pf_merged)*100:.1f}%)")

# ── Also fix is_ipl and is_t20i (they were saved as 0/1 ints, coerce to bool) ─
pf_merged['is_ipl']  = pf_merged['is_ipl'].astype(bool)
pf_merged['is_t20i'] = pf_merged['is_t20i'].astype(bool)
pf_merged['is_legal'] = pf_merged['is_legal'].astype(bool)

# ── Verify striker_id merged correctly by spot-checking ──────────────────────
if 'striker_id' in pf_merged.columns:
    sample = pf_merged[pf_merged['is_ipl']].head(5)
    print(f"\nSample striker_ids (IPL deliveries): {sample['striker_id'].tolist()}")
    print(f"Sample striker_names: {sample['striker_name'].tolist()}")

# ── Save updated pressure_features.csv ───────────────────────────────────────
print(f"\nSaving updated pressure_features.csv ({len(pf_merged):,} rows × {len(pf_merged.columns)} cols) ...")
pf_merged.to_csv(f'{OUT}/pressure_features.csv', index=False)

elapsed = time.time() - t0
print(f"\nDONE in {elapsed:.1f}s")
print(f"Updated columns: {list(pf_merged.columns)}")

