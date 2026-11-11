"""
RR IPL 2027 Selection Pipeline — Phases 20–32
==============================================
Player Pool, Fit Scores, and Rankings.

IMPORTANT DISCLAIMER:
  Availability / auction status is UNKNOWN for ALL players.
  No official IPL 2027 auction data exists yet.
  The final output is a WATCHLIST — Availability Requires Confirmation.
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
DATA_DIR = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\6af3166e7b922_data_pack'
OUT_DIR  = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\results'

IPL_COMP_IDS = {1358, 1715, 2193, 2725, 3298}   # 2022–2026
RR_TEAM_ID   = 3
IPL_2026_COMP_ID = 3298   # most recent IPL season

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def normalize_col(series, low, high, clip=True):
    """Linearly map series from [low, high] → [0, 100]."""
    if clip:
        series = series.clip(lower=low, upper=high)
    rng = high - low
    if rng == 0:
        return pd.Series(50.0, index=series.index)
    return ((series - low) / rng * 100).clip(0, 100)


def inverse_normalize_col(series, low, high, clip=True):
    """Lower is better: map [low, high] → [100, 0]."""
    return 100 - normalize_col(series, low, high, clip)


def safe_div(num, den, fill=0.0):
    """Element-wise safe division."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = np.where(den > 0, num / den, fill)
    return result


# ---------------------------------------------------------------------------
# SECTION 0 — LOAD DATA
# ---------------------------------------------------------------------------
print("=" * 70)
print("SECTION 0 — Loading input data")
print("=" * 70)

def load_csv(path, label):
    if os.path.exists(path):
        df = pd.read_csv(path, low_memory=False)
        print(f"  Loaded {label}: {len(df):,} rows")
        return df
    else:
        print(f"  WARNING: {label} not found at {path}")
        return pd.DataFrame()


bbb = load_csv(os.path.join(DATA_DIR, 'ball_by_ball.csv'), 'ball_by_ball')
matches = load_csv(os.path.join(DATA_DIR, 'matches.csv'), 'matches')
comps = load_csv(os.path.join(DATA_DIR, 'competitions.csv'), 'competitions')
players_csv = load_csv(os.path.join(DATA_DIR, 'players.csv'), 'players')

# Results CSVs (produced by earlier pipeline stages)
rr_weak = load_csv(os.path.join(OUT_DIR, 'rr_weaknesses.csv'), 'rr_weaknesses')
rr_profiles = load_csv(os.path.join(OUT_DIR, 'rr_required_player_profiles.csv'), 'rr_required_player_profiles')
bat_metrics = load_csv(os.path.join(OUT_DIR, 'player_batting_metrics.csv'), 'player_batting_metrics')
bowl_metrics = load_csv(os.path.join(OUT_DIR, 'player_bowling_metrics.csv'), 'player_bowling_metrics')
pressure_metrics = load_csv(os.path.join(OUT_DIR, 'pressure_player_metrics.csv'), 'pressure_player_metrics')
reliability = load_csv(os.path.join(OUT_DIR, 'player_reliability.csv'), 'player_reliability')
role_analysis = load_csv(os.path.join(OUT_DIR, 'player_role_analysis.csv'), 'player_role_analysis')
comp_map = load_csv(os.path.join(OUT_DIR, 'competition_team_player_mapping.csv'), 'competition_team_player_mapping')

# If comp_map not in results, try data_pack
if comp_map.empty:
    comp_map = load_csv(os.path.join(DATA_DIR, 'competition_team_player_mapping.csv'), 'competition_team_player_mapping (data_pack)')

# ---------------------------------------------------------------------------
# SECTION 1 — PLAYER POOL (Phases 20–21)
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 1 — Building player pool (Phases 20–21)")
print("=" * 70)

# --- filter bbb to IPL, non-super-over ---
bbb['innings'] = pd.to_numeric(bbb.get('innings', pd.Series(dtype=float)), errors='coerce')
bbb_ipl = bbb[bbb['innings'].isin([1, 2])].copy() if 'innings' in bbb.columns else bbb.copy()
if 'comp_id' in bbb_ipl.columns:
    bbb_ipl = bbb_ipl[bbb_ipl['comp_id'].isin(IPL_COMP_IDS)].copy()
elif 'match_id' in bbb_ipl.columns and 'comp_id' in matches.columns:
    match_comp = matches[['match_id', 'comp_id']].drop_duplicates()
    bbb_ipl = bbb_ipl.merge(match_comp, on='match_id', how='left', suffixes=('', '_m'))
    comp_col = 'comp_id_m' if 'comp_id_m' in bbb_ipl.columns else 'comp_id'
    bbb_ipl = bbb_ipl[bbb_ipl[comp_col].isin(IPL_COMP_IDS)].copy()

# Merge comp_id into matches if needed
if 'comp_id' not in matches.columns:
    pass  # already merged above or missing

# --- build all_players from comp_map ---
if not comp_map.empty:
    # Try common column names
    pid_col  = next((c for c in ['player_id', 'playerid', 'player'] if c in comp_map.columns), None)
    pname_col = next((c for c in ['player_name', 'playername', 'name'] if c in comp_map.columns), None)
    cid_col  = next((c for c in ['comp_id', 'competition_id', 'compid'] if c in comp_map.columns), None)

    if pid_col and cid_col:
        ipl_comp_map = comp_map[comp_map[cid_col].isin(IPL_COMP_IDS)].copy()
        pool_cols = [pid_col]
        if pname_col:
            pool_cols.append(pname_col)
        all_players = ipl_comp_map[pool_cols].drop_duplicates(subset=[pid_col]).copy()
        all_players.rename(columns={pid_col: 'player_id'}, inplace=True)
        if pname_col:
            all_players.rename(columns={pname_col: 'player_name'}, inplace=True)
        else:
            all_players['player_name'] = 'UNKNOWN'
        print(f"  Total distinct IPL players from comp_map: {len(all_players):,}")
    else:
        print("  WARNING: comp_map missing expected columns. Building from ball_by_ball.")
        all_players = pd.DataFrame()
else:
    all_players = pd.DataFrame()

# Fallback: build from ball_by_ball
if all_players.empty:
    print("  Building player pool from ball_by_ball (batter_id + bowler_id)")
    batters = bbb_ipl[['batter_id']].dropna().rename(columns={'batter_id': 'player_id'})
    bowlers = bbb_ipl[['bowler_id']].dropna().rename(columns={'bowler_id': 'player_id'})
    all_players = pd.concat([batters, bowlers]).drop_duplicates(subset=['player_id']).copy()
    all_players['player_name'] = 'UNKNOWN'
    print(f"  Total distinct IPL players (bbb fallback): {len(all_players):,}")

# Enrich with player names from players.csv if available
if not players_csv.empty:
    p_pid = next((c for c in ['player_id', 'playerid', 'id'] if c in players_csv.columns), None)
    p_pname = next((c for c in ['player_name', 'name', 'full_name'] if c in players_csv.columns), None)
    if p_pid and p_pname:
        name_map = players_csv[[p_pid, p_pname]].drop_duplicates(subset=[p_pid])
        name_map.rename(columns={p_pid: 'player_id', p_pname: 'player_name_lookup'}, inplace=True)
        all_players = all_players.merge(name_map, on='player_id', how='left')
        mask = all_players['player_name'].isna() | (all_players['player_name'] == 'UNKNOWN')
        all_players.loc[mask, 'player_name'] = all_players.loc[mask, 'player_name_lookup']
        all_players.drop(columns=['player_name_lookup'], errors='ignore', inplace=True)

all_players['player_name'] = all_players['player_name'].fillna('UNKNOWN')

# --- Availability: UNKNOWN for all ---
all_players['availability_status'] = 'UNKNOWN'

# --- Nationality & age: UNKNOWN / None ---
all_players['nationality'] = 'UNKNOWN'
all_players['age'] = None

print(f"  Player pool size: {len(all_players):,}")

# ---------------------------------------------------------------------------
# RR 2026 squad: players who appeared in RR's IPL 2026 matches (playing XI)
# ---------------------------------------------------------------------------
print()
print("  Identifying RR 2026 squad members ...")

# Find IPL 2026 match_ids
if 'comp_id' in matches.columns:
    ipl2026_match_ids = set(matches.loc[matches['comp_id'] == IPL_2026_COMP_ID, 'match_id'])
else:
    ipl2026_match_ids = set()
print(f"  IPL 2026 match_ids found: {len(ipl2026_match_ids)}")

# Players who appeared for RR (batting or bowling) in those matches
rr_batter_ids = set()
rr_bowler_ids = set()

if 'comp_id' in bbb.columns:
    rr2026_mask = (
        bbb['comp_id'].isin([IPL_2026_COMP_ID]) &
        bbb['innings'].isin([1, 2])
    )
elif ipl2026_match_ids:
    rr2026_mask = bbb['match_id'].isin(ipl2026_match_ids) & bbb['innings'].isin([1, 2])
else:
    rr2026_mask = pd.Series(False, index=bbb.index)

rr2026_bbb = bbb[rr2026_mask].copy()

# Use playing_eleven, competition_team_player_mapping, and ball_by_ball to find RR 2026 squad
rr26_match_path = os.path.join(OUT_DIR, 'rr_ipl_2026_matches.csv')
if os.path.exists(rr26_match_path):
    rr_matches_df = pd.read_csv(rr26_match_path)
    rr26_match_ids = set(rr_matches_df['match_id'])
else:
    rr26_match_ids = set(matches.loc[
        (matches['comp_id'] == IPL_2026_COMP_ID) &
        ((matches.get('home_team_id', pd.Series()) == RR_TEAM_ID) |
         (matches.get('away_team_id', pd.Series()) == RR_TEAM_ID)),
        'match_id'
    ])

# 1. From comp_map (IPL 2026 squad)
rr26_cmap_ids = set(comp_map.loc[
    (comp_map.get('comp_id', pd.Series()) == IPL_2026_COMP_ID) &
    (comp_map.get('team_id', pd.Series()) == RR_TEAM_ID),
    'player_id'
]) if not comp_map.empty and 'team_id' in comp_map.columns else set()

# 2. From playing_eleven
pe_path = os.path.join(DATA_DIR, 'playing_eleven.csv')
pe_rr26_ids = set()
if os.path.exists(pe_path):
    pe_df = pd.read_csv(pe_path, low_memory=False)
    pe_rr26_ids = set(pe_df.loc[
        (pe_df['match_id'].isin(rr26_match_ids)) &
        (pe_df['team_id'] == RR_TEAM_ID),
        'player_id'
    ].dropna())

# 3. From ball_by_ball (striker_id or bowler_id)
striker_col = 'striker_id' if 'striker_id' in bbb.columns else 'batter_id'
rr_bbb_bat = set(bbb.loc[
    (bbb['match_id'].isin(rr26_match_ids)) &
    (bbb.get('batting_team_id', pd.Series()) == RR_TEAM_ID),
    striker_col
].dropna()) if striker_col in bbb.columns else set()

rr_bbb_bowl = set(bbb.loc[
    (bbb['match_id'].isin(rr26_match_ids)) &
    (bbb.get('bowling_team_id', pd.Series()) == RR_TEAM_ID),
    'bowler_id'
].dropna()) if 'bowler_id' in bbb.columns else set()

rr_squad_2026_ids = rr26_cmap_ids | pe_rr26_ids | rr_bbb_bat | rr_bbb_bowl
print(f"  RR 2026 squad members identified: {len(rr_squad_2026_ids)}")

all_players['rr_squad_2026'] = all_players['player_id'].isin(rr_squad_2026_ids)

# --- played_for_RR_ever ---
# Players who appeared for RR in any IPL season
rr_ever_cmap = set(comp_map.loc[
    (comp_map.get('comp_id', pd.Series()).isin(IPL_COMP_IDS)) &
    (comp_map.get('team_id', pd.Series()) == RR_TEAM_ID),
    'player_id'
]) if not comp_map.empty and 'team_id' in comp_map.columns else set()

rr_ever_batters = set(bbb_ipl.loc[
    bbb_ipl.get('batting_team_id', pd.Series()) == RR_TEAM_ID,
    striker_col
].dropna()) if striker_col in bbb_ipl.columns else set()

rr_ever_bowlers = set(bbb_ipl.loc[
    bbb_ipl.get('bowling_team_id', pd.Series()) == RR_TEAM_ID,
    'bowler_id'
].dropna()) if 'bowler_id' in bbb_ipl.columns else set()

rr_ever_ids = rr_ever_cmap | rr_ever_batters | rr_ever_bowlers
all_players['played_for_RR_ever'] = all_players['player_id'].isin(rr_ever_ids)
print(f"  Players who played for RR (any IPL season): {all_players['played_for_RR_ever'].sum()}")

# ---------------------------------------------------------------------------
# SECTION 2 — NATIONALITY & AGE (already set to UNKNOWN/None above)
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 2 — Nationality & Age (not in datasets — set to UNKNOWN)")
print("=" * 70)
print("  nationality = 'UNKNOWN', age = None for all players.")

# ---------------------------------------------------------------------------
# SECTION 3 — VENUE FIT (Phase 26)
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 3 — Venue Fit (Phase 26)")
print("=" * 70)

# Find Jaipur venue_id: home games for RR in IPL
rr_home_matches = matches[
    (matches['comp_id'].isin(IPL_COMP_IDS)) &
    (matches.get('home_team_id', pd.Series(dtype=float)) == RR_TEAM_ID)
] if 'home_team_id' in matches.columns else pd.DataFrame()

jaipur_venue_ids = set()
guwahati_venue_ids = set()

if not rr_home_matches.empty and 'venue_id' in rr_home_matches.columns:
    venue_counts = rr_home_matches['venue_id'].value_counts()
    # Primary venue = most frequent
    jaipur_venue_ids = {venue_counts.index[0]} if len(venue_counts) > 0 else set()
    # Secondary venue(s) = other home venues
    guwahati_venue_ids = set(venue_counts.index[1:]) if len(venue_counts) > 1 else set()
    print(f"  Jaipur venue_id(s):   {jaipur_venue_ids}")
    print(f"  Guwahati venue_id(s): {guwahati_venue_ids}")
else:
    print("  WARNING: Cannot determine RR home venues from matches data.")

rr_venue_ids = jaipur_venue_ids | guwahati_venue_ids


def compute_venue_metrics(bbb_data, venue_ids, label):
    """Compute average pitch/condition metrics for a set of venue_ids."""
    if not venue_ids or 'venue_id' not in bbb_data.columns:
        return {}
    sub = bbb_data[bbb_data['venue_id'].isin(venue_ids) & bbb_data['innings'].isin([1, 2])].copy()
    if sub.empty:
        return {}
    sub['is_legal'] = (sub['extras_type'].isna() | ~sub['extras_type'].isin(['wide', 'Overstep'])).astype(int) if 'extras_type' in sub.columns else 1
    sub['runs'] = pd.to_numeric(sub.get('runs', 0), errors='coerce').fillna(0)
    sub['is_wicket'] = pd.to_numeric(sub.get('is_wicket', 0), errors='coerce').fillna(0)

    # Average SR at venue = (total batter runs / total legal balls) * 100
    total_legal = sub['is_legal'].sum()
    total_runs = sub['runs'].sum()
    avg_sr = (total_runs / total_legal * 100) if total_legal > 0 else 0

    # Economy
    # Group by bowler to get economy then average
    legal_sub = sub[sub['is_legal'] == 1]
    if 'bowler_id' in legal_sub.columns and not legal_sub.empty:
        bow_grp = legal_sub.groupby('bowler_id').agg(
            balls=('is_legal', 'sum'), runs=('runs', 'sum')
        ).reset_index()
        bow_grp['economy'] = safe_div(bow_grp['runs'] * 6, bow_grp['balls'])
        avg_economy = bow_grp['economy'].mean()
    else:
        avg_economy = avg_sr / 100 * 6  # rough proxy

    # Pace / spin dominance — need bowling_type or bowler category
    pace_dom = 0.5
    spin_dom = 0.5
    if 'bowling_type' in sub.columns:
        type_counts = sub['bowling_type'].value_counts(normalize=True)
        pace_types = [t for t in type_counts.index if any(p in str(t).lower() for p in ['pace', 'fast', 'medium'])]
        spin_types = [t for t in type_counts.index if any(p in str(t).lower() for p in ['spin', 'off', 'leg', 'slow'])]
        pace_dom = type_counts[pace_types].sum() if pace_types else 0.5
        spin_dom = type_counts[spin_types].sum() if spin_types else 0.5

    # Average first innings score
    if 'match_id' in sub.columns:
        first_inn = sub[sub['innings'] == 1].copy()
        first_inn['runs_x'] = pd.to_numeric(first_inn.get('runs', 0), errors='coerce').fillna(0)
        first_inn['ex2']    = pd.to_numeric(first_inn.get('extras_2_runs', 0), errors='coerce').fillna(0)
        first_inn['total_runs'] = first_inn['runs_x'] + first_inn['ex2']
        match_totals = first_inn.groupby('match_id')['total_runs'].sum()
        avg_first_inn = match_totals.mean() if not match_totals.empty else 160.0
    else:
        avg_first_inn = 160.0

    result = {
        f'avg_SR_at_{label}': round(avg_sr, 2),
        f'avg_economy_at_{label}': round(avg_economy, 2),
        f'pace_dominance_{label}': round(pace_dom, 3),
        f'spin_dominance_{label}': round(spin_dom, 3),
        f'avg_first_inn_score_{label}': round(avg_first_inn, 1),
    }
    print(f"  {label} venue metrics: {result}")
    return result


jaipur_venue_metrics = compute_venue_metrics(bbb, jaipur_venue_ids, 'jaipur')
guwahati_venue_metrics = compute_venue_metrics(bbb, guwahati_venue_ids, 'guwahati')


def compute_player_venue_stats(bbb_data, venue_ids, label):
    """Per-player batting SR and bowling economy at given venue(s)."""
    if not venue_ids or 'venue_id' not in bbb_data.columns:
        return pd.DataFrame()
    sub = bbb_data[bbb_data['venue_id'].isin(venue_ids) & bbb_data['innings'].isin([1, 2])].copy()
    if sub.empty:
        return pd.DataFrame()

    sub['is_legal'] = (sub['extras_type'].isna() | ~sub['extras_type'].isin(['wide', 'Overstep'])).astype(int) if 'extras_type' in sub.columns else 1
    sub['runs']     = pd.to_numeric(sub.get('runs', 0), errors='coerce').fillna(0)

    result_parts = []

    if 'batter_id' in sub.columns:
        bat_grp = sub.groupby('batter_id').agg(
            venue_balls_faced=(sub.columns[sub.columns.get_loc('is_legal')], 'sum') if 'is_legal' in sub.columns else ('runs', 'count'),
            venue_runs=('runs', 'sum')
        ).reset_index()
        bat_grp.columns = ['player_id', f'venue_balls_{label}', f'venue_runs_{label}']
        bat_grp[f'venue_bat_SR_{label}'] = safe_div(bat_grp[f'venue_runs_{label}'] * 100, bat_grp[f'venue_balls_{label}'])
        result_parts.append(bat_grp[['player_id', f'venue_bat_SR_{label}', f'venue_balls_{label}']])

    if 'bowler_id' in sub.columns:
        leg = sub[sub['is_legal'] == 1]
        bowl_grp = leg.groupby('bowler_id').agg(
            venue_balls_bowled=('is_legal', 'sum'),
            venue_runs_conceded=('runs', 'sum')
        ).reset_index()
        bowl_grp.columns = ['player_id', f'venue_balls_bowled_{label}', f'venue_runs_conceded_{label}']
        bowl_grp[f'venue_bowl_econ_{label}'] = safe_div(
            bowl_grp[f'venue_runs_conceded_{label}'] * 6,
            bowl_grp[f'venue_balls_bowled_{label}']
        )
        if result_parts:
            result_parts[0] = result_parts[0].merge(
                bowl_grp[['player_id', f'venue_bowl_econ_{label}', f'venue_balls_bowled_{label}']],
                on='player_id', how='outer'
            )
        else:
            result_parts.append(bowl_grp[['player_id', f'venue_bowl_econ_{label}', f'venue_balls_bowled_{label}']])

    if result_parts:
        return result_parts[0]
    return pd.DataFrame()


print("  Computing player venue stats for Jaipur ...")
jaipur_player_stats = compute_player_venue_stats(bbb, jaipur_venue_ids, 'jaipur')
print("  Computing player venue stats for Guwahati ...")
guwahati_player_stats = compute_player_venue_stats(bbb, guwahati_venue_ids, 'guwahati')

# Merge venue stats into all_players
if not jaipur_player_stats.empty:
    all_players = all_players.merge(jaipur_player_stats, on='player_id', how='left')
if not guwahati_player_stats.empty:
    all_players = all_players.merge(guwahati_player_stats, on='player_id', how='left')

# ---------------------------------------------------------------------------
# SECTION 4 — RECENT FORM SCORE (Phase 22)
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 4 — Recent Form Score (Phase 22)")
print("=" * 70)

# Check if batting metrics has season breakdown or just overall
# We need 2026 metrics vs career metrics
# Columns expected: player_id, overall_SR, career_SR (or SR_2026 if available)

def compute_recent_form(bat_m, bowl_m, bbb_data, ipl2026_comp=IPL_2026_COMP_ID):
    """
    Compute recent form from 2026 season vs career.
    Returns a df with player_id, recent_form_bat_raw, recent_form_bowl_raw.
    """
    results = {}

    # --- Batting recent form ---
    # Need 2026 and career SR. Try columns first, then recompute from bbb
    bat_cols = list(bat_m.columns) if not bat_m.empty else []

    # Look for season-specific columns
    has_2026_bat = any('2026' in str(c) for c in bat_cols)
    has_career_bat = 'overall_SR' in bat_cols or 'career_SR' in bat_cols

    if has_2026_bat and has_career_bat:
        sr_2026_col = next(c for c in bat_cols if '2026' in str(c) and 'SR' in str(c).upper())
        career_sr_col = 'career_SR' if 'career_SR' in bat_cols else 'overall_SR'
        rf_bat = bat_m[['player_id', sr_2026_col, career_sr_col]].copy()
        rf_bat.rename(columns={sr_2026_col: 'SR_2026', career_sr_col: 'career_SR'}, inplace=True)
    else:
        # Recompute from ball_by_ball
        bbb_data_copy = bbb_data.copy()
        bbb_data_copy['runs'] = pd.to_numeric(bbb_data_copy.get('runs', 0), errors='coerce').fillna(0)
        bbb_data_copy['is_legal'] = (
            bbb_data_copy['extras_type'].isna() | ~bbb_data_copy['extras_type'].isin(['wide', 'Overstep'])
        ).astype(int) if 'extras_type' in bbb_data_copy.columns else 1

        ipl_bbb = bbb_data_copy[bbb_data_copy.get('comp_id', pd.Series()).isin(IPL_COMP_IDS)].copy() if 'comp_id' in bbb_data_copy.columns else bbb_data_copy.copy()

        # Career stats
        if 'batter_id' in ipl_bbb.columns:
            career_bat = ipl_bbb.groupby('batter_id').agg(
                career_balls=('is_legal', 'sum'), career_runs=('runs', 'sum')
            ).reset_index()
            career_bat.rename(columns={'batter_id': 'player_id'}, inplace=True)
            career_bat['career_SR'] = safe_div(career_bat['career_runs'] * 100, career_bat['career_balls'])

            # 2026 stats
            ipl2026_bbb = ipl_bbb[ipl_bbb.get('comp_id', pd.Series()) == ipl2026_comp] if 'comp_id' in ipl_bbb.columns else pd.DataFrame()
            if ipl2026_bbb.empty and 'match_id' in ipl_bbb.columns:
                m2026_ids = set(matches.loc[matches['comp_id'] == ipl2026_comp, 'match_id']) if 'comp_id' in matches.columns else set()
                ipl2026_bbb = ipl_bbb[ipl_bbb['match_id'].isin(m2026_ids)]

            if not ipl2026_bbb.empty and 'batter_id' in ipl2026_bbb.columns:
                bat_2026 = ipl2026_bbb.groupby('batter_id').agg(
                    balls_2026=('is_legal', 'sum'), runs_2026=('runs', 'sum')
                ).reset_index()
                bat_2026.rename(columns={'batter_id': 'player_id'}, inplace=True)
                bat_2026['SR_2026'] = safe_div(bat_2026['runs_2026'] * 100, bat_2026['balls_2026'])
                rf_bat = career_bat[['player_id', 'career_SR']].merge(bat_2026[['player_id', 'SR_2026', 'balls_2026']], on='player_id', how='outer')
            else:
                rf_bat = career_bat[['player_id', 'career_SR']].copy()
                rf_bat['SR_2026'] = np.nan
                rf_bat['balls_2026'] = 0
        else:
            rf_bat = pd.DataFrame(columns=['player_id', 'career_SR', 'SR_2026'])

    # Compute recent_form_bat
    if not rf_bat.empty and 'SR_2026' in rf_bat.columns and 'career_SR' in rf_bat.columns:
        # If only 1 season or no 2026 data: neutral = 1.0
        rf_bat['recent_form_bat_raw'] = np.where(
            (rf_bat['SR_2026'].isna()) | (rf_bat['career_SR'] <= 0),
            1.0,
            safe_div(rf_bat['SR_2026'], rf_bat['career_SR'], fill=1.0)
        )
        rf_bat['recent_form_bat_raw'] = rf_bat['recent_form_bat_raw'].clip(0.5, 2.0)
        results['bat'] = rf_bat[['player_id', 'recent_form_bat_raw']].copy()

    # --- Bowling recent form ---
    bowl_cols = list(bowl_m.columns) if not bowl_m.empty else []
    has_2026_bowl = any('2026' in str(c) for c in bowl_cols)

    bbb_data_copy2 = bbb_data.copy()
    bbb_data_copy2['runs'] = pd.to_numeric(bbb_data_copy2.get('runs', 0), errors='coerce').fillna(0)
    bbb_data_copy2['is_legal'] = (
        bbb_data_copy2['extras_type'].isna() | ~bbb_data_copy2['extras_type'].isin(['wide', 'Overstep'])
    ).astype(int) if 'extras_type' in bbb_data_copy2.columns else 1

    ipl_bbb2 = bbb_data_copy2[bbb_data_copy2.get('comp_id', pd.Series()).isin(IPL_COMP_IDS)].copy() if 'comp_id' in bbb_data_copy2.columns else bbb_data_copy2.copy()

    if 'bowler_id' in ipl_bbb2.columns:
        legal_ipl2 = ipl_bbb2[ipl_bbb2['is_legal'] == 1]
        career_bowl = legal_ipl2.groupby('bowler_id').agg(
            career_bowl_balls=('is_legal', 'sum'), career_bowl_runs=('runs', 'sum')
        ).reset_index()
        career_bowl.rename(columns={'bowler_id': 'player_id'}, inplace=True)
        career_bowl['career_economy'] = safe_div(career_bowl['career_bowl_runs'] * 6, career_bowl['career_bowl_balls'])

        ipl2026_bbb2 = ipl_bbb2[ipl_bbb2.get('comp_id', pd.Series()) == ipl2026_comp] if 'comp_id' in ipl_bbb2.columns else pd.DataFrame()
        if ipl2026_bbb2.empty and 'match_id' in ipl_bbb2.columns:
            m2026_ids2 = set(matches.loc[matches['comp_id'] == ipl2026_comp, 'match_id']) if 'comp_id' in matches.columns else set()
            ipl2026_bbb2 = ipl_bbb2[ipl_bbb2['match_id'].isin(m2026_ids2)]

        if not ipl2026_bbb2.empty and 'bowler_id' in ipl2026_bbb2.columns:
            legal_2026_2 = ipl2026_bbb2[ipl2026_bbb2['is_legal'] == 1]
            bowl_2026 = legal_2026_2.groupby('bowler_id').agg(
                balls_2026=('is_legal', 'sum'), runs_2026=('runs', 'sum')
            ).reset_index()
            bowl_2026.rename(columns={'bowler_id': 'player_id'}, inplace=True)
            bowl_2026['economy_2026'] = safe_div(bowl_2026['runs_2026'] * 6, bowl_2026['balls_2026'])
            rf_bowl = career_bowl[['player_id', 'career_economy']].merge(bowl_2026[['player_id', 'economy_2026', 'balls_2026']], on='player_id', how='outer')
        else:
            rf_bowl = career_bowl[['player_id', 'career_economy']].copy()
            rf_bowl['economy_2026'] = np.nan

        rf_bowl['recent_form_bowl_raw'] = np.where(
            (rf_bowl['economy_2026'].isna()) | (rf_bowl['economy_2026'] <= 0),
            1.0,
            safe_div(rf_bowl['career_economy'], rf_bowl['economy_2026'], fill=1.0)
        )
        rf_bowl['recent_form_bowl_raw'] = rf_bowl['recent_form_bowl_raw'].clip(0.5, 2.0)
        results['bowl'] = rf_bowl[['player_id', 'recent_form_bowl_raw']].copy()

    return results


recent_form_data = compute_recent_form(bat_metrics, bowl_metrics, bbb)

if 'bat' in recent_form_data:
    all_players = all_players.merge(recent_form_data['bat'], on='player_id', how='left')
    all_players['recent_form_bat_raw'] = all_players['recent_form_bat_raw'].fillna(1.0)
else:
    all_players['recent_form_bat_raw'] = 1.0

if 'bowl' in recent_form_data:
    all_players = all_players.merge(recent_form_data['bowl'], on='player_id', how='left')
    all_players['recent_form_bowl_raw'] = all_players['recent_form_bowl_raw'].fillna(1.0)
else:
    all_players['recent_form_bowl_raw'] = 1.0

# Normalize recent form to [0, 100]
all_players['recent_form_bat_score']  = normalize_col(all_players['recent_form_bat_raw'],  0.5, 2.0)
all_players['recent_form_bowl_score'] = normalize_col(all_players['recent_form_bowl_raw'], 0.5, 2.0)

print(f"  Recent form scores computed.")

# ---------------------------------------------------------------------------
# SECTION 5 — YOUNG PLAYER FLAG (Phase 27)
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 5 — Young Player Flag (Phase 27)")
print("=" * 70)

# First IPL season from comp_map
if not comp_map.empty:
    pid_col  = next((c for c in ['player_id', 'playerid', 'player'] if c in comp_map.columns), None)
    cid_col  = next((c for c in ['comp_id', 'competition_id', 'compid'] if c in comp_map.columns), None)
    sea_col  = next((c for c in ['season', 'year', 'comp_year'] if c in comp_map.columns), None)

    if pid_col and cid_col:
        ipl_cm = comp_map[comp_map[cid_col].isin(IPL_COMP_IDS)].copy()
        # Map comp_id to season year
        comp_season_map = {1358: 2022, 1715: 2023, 2193: 2024, 2725: 2025, 3298: 2026}
        ipl_cm['_season'] = ipl_cm[cid_col].map(comp_season_map)

        if sea_col:
            ipl_cm['_season'] = ipl_cm['_season'].fillna(pd.to_numeric(ipl_cm[sea_col], errors='coerce'))

        player_seasons = ipl_cm.groupby(pid_col).agg(
            first_ipl_season=('_season', 'min'),
            seasons_in_ipl=('_season', 'nunique')
        ).reset_index().rename(columns={pid_col: 'player_id'})
        all_players = all_players.merge(player_seasons, on='player_id', how='left')
    else:
        all_players['first_ipl_season'] = None
        all_players['seasons_in_ipl'] = 1
else:
    # Fallback: infer from bbb comp_id
    if 'comp_id' in bbb_ipl.columns:
        comp_season_map = {1358: 2022, 1715: 2023, 2193: 2024, 2725: 2025, 3298: 2026}
        bbb_ipl2 = bbb_ipl.copy()
        bbb_ipl2['_season'] = bbb_ipl2['comp_id'].map(comp_season_map)

        batter_seasons = pd.DataFrame()
        bowler_seasons = pd.DataFrame()
        if 'batter_id' in bbb_ipl2.columns:
            batter_seasons = bbb_ipl2.groupby('batter_id')['_season'].agg(['min', 'nunique']).reset_index()
            batter_seasons.columns = ['player_id', 'first_ipl_season', 'seasons_in_ipl']
        if 'bowler_id' in bbb_ipl2.columns:
            bowler_seasons = bbb_ipl2.groupby('bowler_id')['_season'].agg(['min', 'nunique']).reset_index()
            bowler_seasons.columns = ['player_id', 'first_ipl_season', 'seasons_in_ipl']

        ps = pd.concat([batter_seasons, bowler_seasons]).groupby('player_id').agg(
            first_ipl_season=('first_ipl_season', 'min'),
            seasons_in_ipl=('seasons_in_ipl', 'max')
        ).reset_index()
        all_players = all_players.merge(ps, on='player_id', how='left')
    else:
        all_players['first_ipl_season'] = None
        all_players['seasons_in_ipl'] = 1

all_players['first_ipl_season'] = pd.to_numeric(all_players['first_ipl_season'], errors='coerce')
all_players['seasons_in_ipl']   = pd.to_numeric(all_players['seasons_in_ipl'],   errors='coerce').fillna(1)
all_players['is_young'] = all_players['first_ipl_season'] >= 2024
print(f"  Young players (debut >= 2024): {all_players['is_young'].sum()}")

# Upside score for young players
# Components: pressure performance, recent form, role fit (computed later), sample, recency
# We'll compute partial upside now and add role component later

def compute_upside_partial(row, pressure_df):
    """Compute upside score without role fit component (added later)."""
    pid = row['player_id']
    seasons = max(1, row.get('seasons_in_ipl', 1))

    # Pressure component: use pressure_SR if batter, else pressure_economy (inverted)
    pres_score = 50.0
    if not pressure_df.empty:
        pid_col_p = 'player_id' if 'player_id' in pressure_df.columns else pressure_df.columns[0]
        prow = pressure_df[pressure_df[pid_col_p] == pid]
        if not prow.empty:
            prow = prow.iloc[0]
            if 'pressure_SR' in prow and not pd.isna(prow['pressure_SR']):
                pres_score = normalize_col(pd.Series([prow['pressure_SR']]), 50, 200).iloc[0]
            elif 'pressure_economy' in prow and not pd.isna(prow['pressure_economy']):
                pres_score = inverse_normalize_col(pd.Series([prow['pressure_economy']]), 6, 14).iloc[0]

    recent_form = row.get('recent_form_bat_score', row.get('recent_form_bowl_score', 50.0))
    if pd.isna(recent_form):
        recent_form = 50.0
    recent_norm = recent_form  # already 0-100

    recency_score = 100.0 / (seasons + 1) * 10  # max ~50 for new player

    upside = (
        0.30 * pres_score +
        0.25 * recent_norm +
        0.15 * 50.0 +           # role fit placeholder, filled later
        0.15 * min(100, 50.0) + # sample placeholder
        0.10 * recency_score * 10
    )
    return min(100, max(0, upside))


# Merge pressure metrics into all_players for computation
pres_pid_col = 'player_id' if not pressure_metrics.empty and 'player_id' in pressure_metrics.columns else None

if pres_pid_col and not pressure_metrics.empty:
    # Keep key pressure columns
    keep_pres = ['player_id']
    for col in ['pressure_SR', 'pressure_economy', 'pressure_avg', 'pressure_delta_SR',
                 'pressure_delta_economy', 'pressure_wicket_rate', 'pressure_dot_rate',
                 'high_RRR_SR', 'close_match_SR', 'post_wicket_SR',
                 'death_pressure_economy', 'high_RRR_economy', 'confidence_score',
                 'balls_faced_pressure', 'balls_bowled_pressure']:
        if col in pressure_metrics.columns:
            keep_pres.append(col)
    all_players = all_players.merge(pressure_metrics[keep_pres].drop_duplicates('player_id'), on='player_id', how='left')

# Compute upside scores (vectorized approximation)
upside_parts = {}
seasons_arr = all_players['seasons_in_ipl'].fillna(1).values
recency_arr = 100.0 / (seasons_arr + 1) * 10

pres_arr = np.where(
    all_players.get('pressure_SR', pd.Series(np.nan, index=all_players.index)).notna(),
    normalize_col(all_players.get('pressure_SR', pd.Series(50.0, index=all_players.index)).fillna(50), 50, 200).values,
    np.where(
        all_players.get('pressure_economy', pd.Series(np.nan, index=all_players.index)).notna(),
        inverse_normalize_col(all_players.get('pressure_economy', pd.Series(9.0, index=all_players.index)).fillna(9), 6, 14).values,
        50.0
    )
)

recent_arr = np.where(
    all_players['recent_form_bat_score'].notna(),
    all_players['recent_form_bat_score'].fillna(50).values,
    all_players['recent_form_bowl_score'].fillna(50).values
)

all_players['upside_score_partial'] = np.clip(
    0.30 * pres_arr + 0.25 * recent_arr + 0.15 * 50 + 0.15 * 50 + 0.10 * recency_arr,
    0, 100
)
print("  Upside scores (partial) computed.")

# ---------------------------------------------------------------------------
# SECTION 6 — PLAYER FIT SCORE (Phase 22)
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 6 — Player Fit Score (Phase 22)")
print("=" * 70)

# --- Merge in reliability ---
rel_pid_col = None
if not reliability.empty:
    rel_pid_col = next((c for c in ['player_id', 'playerid'] if c in reliability.columns), None)
    if rel_pid_col:
        keep_rel = [rel_pid_col]
        for col in ['reliability_score', 'reliability_score_bat', 'reliability_score_bowl',
                    'confidence_score', 'confidence_score_bat', 'confidence_score_bowl']:
            if col in reliability.columns:
                keep_rel.append(col)
        all_players = all_players.merge(
            reliability[keep_rel].drop_duplicates(rel_pid_col).rename(columns={rel_pid_col: 'player_id'}),
            on='player_id', how='left', suffixes=('', '_rel')
        )

# Unify reliability & confidence columns
def pick_col(df, *candidates, default=50.0):
    for c in candidates:
        if c in df.columns:
            return df[c].fillna(default)
    return pd.Series(default, index=df.index)

all_players['reliability_score_unified'] = pick_col(all_players,
    'reliability_score', 'reliability_score_bat', 'reliability_score_bowl')
all_players['confidence_score_unified']  = pick_col(all_players,
    'confidence_score', 'confidence_score_bat', 'confidence_score_bowl')

# Normalize reliability to [0, 100] (may already be 0-100 or 0-1)
max_rel = all_players['reliability_score_unified'].max()
if max_rel <= 1.0 and max_rel > 0:
    all_players['reliability_norm'] = all_players['reliability_score_unified'] * 100
else:
    all_players['reliability_norm'] = all_players['reliability_score_unified'].clip(0, 100)

max_conf = all_players['confidence_score_unified'].max()
if max_conf <= 1.0 and max_conf > 0:
    all_players['confidence_norm'] = all_players['confidence_score_unified'] * 100
else:
    all_players['confidence_norm'] = all_players['confidence_score_unified'].clip(0, 100)

# --- Merge batting & bowling metrics ---
if not bat_metrics.empty:
    bat_pid = next((c for c in ['player_id', 'playerid', 'striker_id'] if c in bat_metrics.columns), None)
    if bat_pid:
        all_players = all_players.merge(
            bat_metrics.drop_duplicates(bat_pid).rename(columns={bat_pid: 'player_id'}),
            on='player_id', how='left', suffixes=('', '_bat')
        )

if not bowl_metrics.empty:
    bowl_pid = next((c for c in ['player_id', 'playerid', 'bowler_id'] if c in bowl_metrics.columns), None)
    if bowl_pid:
        all_players = all_players.merge(
            bowl_metrics.drop_duplicates(bowl_pid).rename(columns={bowl_pid: 'player_id'}),
            on='player_id', how='left', suffixes=('', '_bowl')
        )

# --- Merge role analysis ---
if not role_analysis.empty:
    role_pid = next((c for c in ['player_id', 'playerid'] if c in role_analysis.columns), None)
    if role_pid:
        keep_role = [role_pid]
        for col in ['determined_role', 'primary_role', 'role', 'primary_batting_role',
                    'is_batter', 'is_bowler', 'is_allrounder', 'balls_faced', 'balls_bowled']:
            if col in role_analysis.columns:
                keep_role.append(col)
        all_players = all_players.merge(
            role_analysis[keep_role].drop_duplicates(role_pid).rename(columns={role_pid: 'player_id'}),
            on='player_id', how='left', suffixes=('', '_role')
        )

# Determine determined_role from available columns
if 'determined_role' not in all_players.columns:
    if 'primary_role' in all_players.columns:
        all_players['determined_role'] = all_players['primary_role']
    elif 'role' in all_players.columns:
        all_players['determined_role'] = all_players['role']
    else:
        all_players['determined_role'] = 'Unknown'

all_players['determined_role'] = all_players['determined_role'].fillna('Unknown')

# --- COMPONENT A: Pressure Performance Score (25%) ---
print("  Computing Component A: Pressure Performance Score ...")

# Batter pressure score
pres_bat_components = {}
for col, weight, direction in [
    ('pressure_SR', 0.3, 'normal'),
    ('pressure_avg', 0.15, 'normal'),
    ('pressure_delta_SR', 0.2, 'normal'),
    ('high_RRR_SR', 0.15, 'normal'),
    ('close_match_SR', 0.1, 'normal'),
    ('post_wicket_SR', 0.1, 'normal'),
]:
    if col in all_players.columns:
        s = all_players[col].fillna(all_players[col].median() if all_players[col].notna().any() else 0)
        if direction == 'normal':
            pres_bat_components[col] = (normalize_col(s, s.quantile(0.1), s.quantile(0.9)).values, weight)
        else:
            pres_bat_components[col] = (inverse_normalize_col(s, s.quantile(0.1), s.quantile(0.9)).values, weight)

if pres_bat_components:
    total_weight = sum(w for _, w in pres_bat_components.values())
    pressure_bat_score = sum(arr * w for arr, w in pres_bat_components.values()) / total_weight
else:
    pressure_bat_score = np.full(len(all_players), 50.0)

# Bowler pressure score
pres_bowl_components = {}
for col, weight, direction in [
    ('pressure_economy', 0.25, 'inverse'),
    ('pressure_wicket_rate', 0.2, 'normal'),
    ('pressure_dot_rate', 0.15, 'normal'),
    ('death_pressure_economy', 0.15, 'inverse'),
    ('high_RRR_economy', 0.15, 'inverse'),
    ('pressure_delta_economy', 0.1, 'inverse'),
]:
    if col in all_players.columns:
        s = all_players[col].fillna(all_players[col].median() if all_players[col].notna().any() else 0)
        if direction == 'inverse':
            pres_bowl_components[col] = (inverse_normalize_col(s, s.quantile(0.1), s.quantile(0.9)).values, weight)
        else:
            pres_bowl_components[col] = (normalize_col(s, s.quantile(0.1), s.quantile(0.9)).values, weight)

if pres_bowl_components:
    total_weight_b = sum(w for _, w in pres_bowl_components.values())
    pressure_bowl_score = sum(arr * w for arr, w in pres_bowl_components.values()) / total_weight_b
else:
    pressure_bowl_score = np.full(len(all_players), 50.0)

# Combine: use batting for batters/allrounders, bowling for bowlers
role_series = all_players['determined_role'].str.lower()
is_batter_role  = role_series.str.contains('bat|open|finisher', na=False)
is_bowler_role  = role_series.str.contains('bowl|spin|pace|fast|medium', na=False)
is_ar_role      = role_series.str.contains('all.round|ar|allround', na=False)

component_A = np.where(
    is_bowler_role & ~is_ar_role,
    pressure_bowl_score,
    np.where(
        is_ar_role,
        0.5 * pressure_bat_score + 0.5 * pressure_bowl_score,
        pressure_bat_score
    )
)
all_players['pressure_score'] = np.clip(component_A, 0, 100)
print(f"  Component A done. Mean pressure score: {all_players['pressure_score'].mean():.1f}")

# --- COMPONENT B: RR Weakness Fit Score (20%) ---
print("  Computing Component B: RR Weakness Fit Score ...")

weakness_fit_scores = np.full(len(all_players), 50.0)
primary_weakness_addressed = [''] * len(all_players)

if not rr_weak.empty:
    # Identify weakness columns
    weak_cat_col  = next((c for c in ['weakness_category', 'category', 'metric', 'weakness'] if c in rr_weak.columns), None)
    weak_rr_col   = next((c for c in ['rr_value', 'rr_stat', 'rr_avg', 'value'] if c in rr_weak.columns), None)
    weak_ipl_col  = next((c for c in ['ipl_avg', 'ipl_benchmark', 'league_avg'] if c in rr_weak.columns), None)
    weak_score_col = next((c for c in ['weakness_score', 'score', 'severity_score'] if c in rr_weak.columns), None)
    weak_rank_col = next((c for c in ['rank', 'weakness_rank'] if c in rr_weak.columns), None)

    if weak_cat_col:
        # Sort by severity / rank
        if weak_score_col:
            rr_weak_sorted = rr_weak.sort_values(weak_score_col, ascending=False).reset_index(drop=True)
        elif weak_rank_col:
            rr_weak_sorted = rr_weak.sort_values(weak_rank_col).reset_index(drop=True)
        else:
            rr_weak_sorted = rr_weak.reset_index(drop=True)

        top3_weaknesses = rr_weak_sorted.head(3)

        # Map weakness categories to player metric columns
        WEAKNESS_TO_METRIC = {
            # death pressure bowling
            'death_pressure': 'death_pressure_economy',
            'death_economy': 'death_economy',
            'highrrr_bowling': 'high_RRR_economy',
            'vs_lhb': 'economy_vs_LHB',
            'vs_rhb': 'economy_vs_RHB',
            'economy': 'economy',
            # batting weaknesses
            'high_rrr': 'high_RRR_SR',
            'phase_death': 'death_SR',
            'death': 'death_SR',
            'phase_middle': 'middle_SR',
            'middle': 'middle_SR',
            'phase_powerplay': 'powerplay_SR',
            'powerplay': 'powerplay_SR',
            'vs_spin': 'SR_vs_spin',
            'vs_pace': 'SR_vs_pace',
            'chasing': 'chasing_SR',
            'post_wicket': 'post_wicket_SR',
            'pressure': 'pressure_SR',
        }

        weakness_fit_scores = np.zeros(len(all_players))
        weights_sum = 0.0

        for idx, weak_row in top3_weaknesses.iterrows():
            category = str(weak_row[weak_cat_col]).lower().strip().replace(' ', '_')
            rr_val = pd.to_numeric(weak_row.get(weak_rr_col, np.nan), errors='coerce') if weak_rr_col else np.nan
            ipl_avg_val = pd.to_numeric(weak_row.get(weak_ipl_col, np.nan), errors='coerce') if weak_ipl_col else np.nan
            weak_weight = pd.to_numeric(weak_row.get(weak_score_col, 1.0), errors='coerce') if weak_score_col else 1.0
            if pd.isna(weak_weight) or weak_weight <= 0:
                weak_weight = 1.0

            # Find matching player metric
            metric_col = None
            for key, col in WEAKNESS_TO_METRIC.items():
                if key in category:
                    if col in all_players.columns:
                        metric_col = col
                    break

            if metric_col is None:
                # Try direct column match
                for c in all_players.columns:
                    if category in c.lower():
                        metric_col = c
                        break

            if metric_col in all_players.columns:
                is_bowling_metric = any(w in metric_col.lower() for w in ['economy', 'econ', 'concede'])
                s = pd.to_numeric(all_players[metric_col], errors='coerce')
                med = s.dropna().median() if s.notna().any() else (9.0 if is_bowling_metric else 140.0)
                filled = s.fillna(med)

                if is_bowling_metric:
                    # Lower economy is better: map 6.0 (great) to 12.0 (poor) -> [100, 0]
                    raw = inverse_normalize_col(filled, 6.5, 11.5)
                else:
                    # Higher SR is better: map 100 to 200 -> [0, 100]
                    raw = normalize_col(filled, 110.0, 190.0)

                raw = np.clip(raw, 0, 100)
                weakness_fit_scores = weakness_fit_scores + raw.values * weak_weight
                weights_sum += weak_weight

                # Track primary weakness for top address
                if idx == 0:
                    primary_weakness_addressed = [str(weak_row[weak_cat_col])] * len(all_players)

        if weights_sum > 0:
            weakness_fit_scores = np.clip(weakness_fit_scores / weights_sum, 0, 100)
        else:
            weakness_fit_scores = np.full(len(all_players), 50.0)

all_players['weakness_fit_score'] = weakness_fit_scores
all_players['primary_weakness_addressed'] = primary_weakness_addressed
print(f"  Component B done. Mean weakness fit: {all_players['weakness_fit_score'].mean():.1f}")

# --- COMPONENT C: Role Fit Score (15%) ---
print("  Computing Component C: Role Fit Score ...")

required_roles = set()
if not rr_profiles.empty:
    role_col_p = next((c for c in ['required_roles', 'role', 'player_role', 'required_role', 'position'] if c in rr_profiles.columns), None)
    if role_col_p:
        for item in rr_profiles[role_col_p].dropna():
            item_str = str(item).replace('[', '').replace(']', '').replace("'", "").replace('"', '').lower()
            for r in item_str.split(','):
                r_clean = r.strip()
                if r_clean:
                    required_roles.add(r_clean)

ADJACENT_ROLES = {
    'middle-order batter': ['finisher', 'allrounder', 'number 4', 'number 5'],
    'finisher': ['middle-order batter', 'hard hitter', 'number 6', 'number 7'],
    'opener': ['top order', 'opening batter'],
    'pace bowler': ['seam bowler', 'medium pace', 'fast bowler', 'death bowler'],
    'death bowler': ['pace bowler', 'fast bowler', 'middle-over bowler'],
    'spin bowler': ['left arm spinner', 'right arm spinner', 'off-break', 'leg-break', 'spinner'],
    'spinner': ['spin bowler', 'slow left', 'off-break', 'leg-break'],
    'allrounder': ['batting allrounder', 'bowling allrounder', 'batting all-rounder', 'bowling all-rounder'],
}


def role_fit(player_role, required_roles):
    if not required_roles or not player_role or player_role == 'Unknown':
        return 50.0
    pr = str(player_role).lower()
    for rr in required_roles:
        if rr in pr or pr in rr:
            return 100.0
    for canon, adjacents in ADJACENT_ROLES.items():
        if canon in pr:
            for adj in adjacents:
                if any(adj in str(rr) for rr in required_roles):
                    return 60.0
    return 30.0


all_players['role_fit_score'] = all_players['determined_role'].apply(
    lambda r: role_fit(r, required_roles)
)
print(f"  Component C done. Mean role fit: {all_players['role_fit_score'].mean():.1f}")

# --- COMPONENT D: IPL Performance Score (10%) ---
print("  Computing Component D: IPL Performance Score ...")

# Batting: normalize overall_SR
overall_sr_col = next((c for c in ['strike_rate', 'overall_SR', 'career_SR', 'batting_SR', 'SR'] if c in all_players.columns), None)
overall_econ_col = next((c for c in ['economy', 'overall_economy', 'career_economy', 'bowling_economy'] if c in all_players.columns), None)

ipl_perf_bat  = normalize_col(pd.to_numeric(all_players[overall_sr_col], errors='coerce').fillna(130) if overall_sr_col else pd.Series(50, index=all_players.index), 100, 200)
ipl_perf_bowl = inverse_normalize_col(pd.to_numeric(all_players[overall_econ_col], errors='coerce').fillna(9.0) if overall_econ_col else pd.Series(9, index=all_players.index), 6.5, 11.5)

all_players['ipl_performance_score'] = np.clip(
    np.where(
        is_bowler_role & ~is_ar_role,
        ipl_perf_bowl,
        np.where(is_ar_role, 0.5 * ipl_perf_bat + 0.5 * ipl_perf_bowl, ipl_perf_bat)
    ),
    0, 100
)
print(f"  Component D done. Mean IPL performance: {all_players['ipl_performance_score'].mean():.1f}")

# --- COMPONENT E: Recent Form Score (10%) ---
# Already computed in Section 4
all_players['recent_form_score'] = np.clip(
    np.where(
        is_bowler_role & ~is_ar_role,
        all_players['recent_form_bowl_score'],
        all_players['recent_form_bat_score']
    ),
    0, 100
)

# --- COMPONENT F: Reliability Score (8%) ---
# Already in reliability_norm
all_players['f_reliability'] = all_players['reliability_norm'].fillna(50)

# --- COMPONENT G: Venue Fit Score (5%) ---
print("  Computing Component G: Venue Fit Score ...")

jaipur_sr_col  = 'venue_bat_SR_jaipur'  if 'venue_bat_SR_jaipur'  in all_players.columns else None
jaipur_econ_col = 'venue_bowl_econ_jaipur' if 'venue_bowl_econ_jaipur' in all_players.columns else None
jaipur_balls_col = 'venue_balls_jaipur' if 'venue_balls_jaipur' in all_players.columns else None

avg_sr_jaipur = jaipur_venue_metrics.get('avg_SR_at_jaipur', 130)
avg_econ_jaipur = jaipur_venue_metrics.get('avg_economy_at_jaipur', 9.0)

venue_bat_score  = pd.Series(50.0, index=all_players.index)
venue_bowl_score = pd.Series(50.0, index=all_players.index)

if jaipur_sr_col:
    # Performance at venue vs avg; default to 0.5 if < 12 deliveries
    has_enough = (all_players.get(jaipur_balls_col, pd.Series(0, index=all_players.index)) >= 12) if jaipur_balls_col else pd.Series(False, index=all_players.index)
    raw_bat_venue = normalize_col(all_players[jaipur_sr_col].fillna(avg_sr_jaipur), avg_sr_jaipur * 0.6, avg_sr_jaipur * 1.4)
    # Pitch type match (spin vs pace preference of player)
    pitch_type_bat = pd.Series(50.0, index=all_players.index)  # neutral default
    venue_bat_score = np.where(has_enough, 0.6 * raw_bat_venue + 0.4 * pitch_type_bat, 50.0)

if jaipur_econ_col:
    jaipur_bowl_balls_col = 'venue_balls_bowled_jaipur' if 'venue_balls_bowled_jaipur' in all_players.columns else None
    has_enough_bowl = (all_players.get(jaipur_bowl_balls_col, pd.Series(0, index=all_players.index)) >= 12) if jaipur_bowl_balls_col else pd.Series(False, index=all_players.index)
    raw_bowl_venue = inverse_normalize_col(all_players[jaipur_econ_col].fillna(avg_econ_jaipur), avg_econ_jaipur * 0.7, avg_econ_jaipur * 1.3)
    pitch_type_bowl = pd.Series(50.0, index=all_players.index)
    venue_bowl_score = np.where(has_enough_bowl, 0.6 * raw_bowl_venue + 0.4 * pitch_type_bowl, 50.0)

all_players['venue_fit_score'] = np.clip(
    np.where(is_bowler_role & ~is_ar_role, venue_bowl_score, venue_bat_score),
    0, 100
)
print(f"  Component G done. Mean venue fit: {all_players['venue_fit_score'].mean():.1f}")

# --- COMPONENT H: Age/Upside Score (4%) ---
print("  Computing Component H: Age/Upside Score ...")

# Finalize upside score using role fit
all_players['upside_score_partial'] = all_players.get('upside_score_partial', pd.Series(50.0, index=all_players.index))

# Add role component to upside
role_fit_arr = all_players['role_fit_score'].values
pres_arr2 = all_players['pressure_score'].values
recent_arr2 = all_players['recent_form_score'].values

balls_faced_col = next((c for c in ['balls_faced', 'total_balls_faced'] if c in all_players.columns), None)
balls_bowled_col = next((c for c in ['balls_bowled', 'total_balls_bowled'] if c in all_players.columns), None)
sample_arr = np.zeros(len(all_players))
if balls_faced_col:
    sample_arr += normalize_col(all_players[balls_faced_col].fillna(0), 0, 500).values
if balls_bowled_col:
    sample_arr += normalize_col(all_players[balls_bowled_col].fillna(0), 0, 500).values
sample_arr = np.clip(sample_arr / max(1, (1 if balls_faced_col else 0) + (1 if balls_bowled_col else 0)), 0, 100)

recency_arr2 = 100.0 / (all_players['seasons_in_ipl'].fillna(1).values + 1) * 10

all_players['upside_score'] = np.clip(
    0.30 * pres_arr2 + 0.25 * recent_arr2 + 0.20 * role_fit_arr + 0.15 * sample_arr + 0.10 * recency_arr2,
    0, 100
)

career_longevity = np.where(all_players['seasons_in_ipl'] >= 3, 70.0, 50.0)
all_players['age_upside_score'] = np.where(
    all_players['is_young'],
    all_players['upside_score'],
    career_longevity
)
print(f"  Component H done. Young players: {all_players['is_young'].sum()}")

# --- COMPONENT I: Availability Confidence (3%) ---
all_players['availability_score'] = 50.0  # UNKNOWN for all

# --- FINAL FIT SCORE ---
print("  Computing final RR Fit Score ...")

all_players['RR_FIT_SCORE_raw'] = (
    0.25 * all_players['pressure_score'] +
    0.20 * all_players['weakness_fit_score'] +
    0.15 * all_players['role_fit_score'] +
    0.10 * all_players['ipl_performance_score'] +
    0.10 * all_players['recent_form_score'] +
    0.08 * all_players['f_reliability'] +
    0.05 * all_players['venue_fit_score'] +
    0.04 * all_players['age_upside_score'] +
    0.03 * all_players['availability_score']
)

# Confidence adjustment
conf = all_players['confidence_norm'].fillna(50)
all_players['RR_FIT_SCORE'] = all_players['RR_FIT_SCORE_raw'] * np.sqrt(conf / 100)
all_players['RR_FIT_SCORE'] = all_players['RR_FIT_SCORE'].clip(0, 100)

print(f"  RR Fit Score computed. Mean: {all_players['RR_FIT_SCORE'].mean():.1f}, Max: {all_players['RR_FIT_SCORE'].max():.1f}")

# --- Minimum data filter ---
# Need 30 balls faced OR 30 balls bowled
has_bat_data = (all_players.get(balls_faced_col, pd.Series(0, index=all_players.index)).fillna(0) >= 30) if balls_faced_col else pd.Series(True, index=all_players.index)
has_bowl_data = (all_players.get(balls_bowled_col, pd.Series(0, index=all_players.index)).fillna(0) >= 30) if balls_bowled_col else pd.Series(True, index=all_players.index)
all_players['has_min_data'] = has_bat_data | has_bowl_data

print(f"  Players with minimum data (30+ balls): {all_players['has_min_data'].sum():,}")

# Save all players with fit scores
all_players.to_csv(os.path.join(OUT_DIR, 'player_fit_scores.csv'), index=False)
print(f"  Saved player_fit_scores.csv ({len(all_players):,} rows)")

# ---------------------------------------------------------------------------
# SECTION 7 — RANKINGS (Phases 29–30)
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 7 — Rankings (Phases 29–30)")
print("=" * 70)

# Non-RR candidates only (exclude RR 2026 squad)
candidates = all_players[
    (~all_players['rr_squad_2026']) &
    (all_players['has_min_data'])
].copy()

print(f"  Candidate pool (non-RR, has data): {len(candidates):,}")

# Sort by RR_FIT_SCORE
candidates = candidates.sort_values('RR_FIT_SCORE', ascending=False).reset_index(drop=True)
candidates['rank'] = candidates.index + 1

# Risk level
def risk_level(conf):
    if conf < 40:
        return 'HIGH'
    elif conf < 70:
        return 'MEDIUM'
    return 'LOW'

candidates['risk_level'] = candidates['confidence_norm'].fillna(50).apply(risk_level)

# Primary reason (data-driven)
def build_primary_reason(row):
    pw = str(row.get('primary_weakness_addressed', ''))
    if not pw or pw == '':
        pw = 'overall performance'
    ps = row.get('pressure_score', 0)
    rr_stat_val = None
    ipl_stat_val = None

    # Try to get the actual stat
    if not rr_weak.empty and 'weakness_category' in rr_weak.columns:
        top_weak = rr_weak.iloc[0] if len(rr_weak) > 0 else None
        if top_weak is not None:
            rr_stat_col  = next((c for c in ['rr_value', 'rr_stat', 'rr_avg', 'value'] if c in rr_weak.columns), None)
            ipl_stat_col = next((c for c in ['ipl_avg', 'ipl_benchmark', 'league_avg'] if c in rr_weak.columns), None)
            rr_stat_val  = top_weak[rr_stat_col] if rr_stat_col else 'N/A'
            ipl_stat_val = top_weak[ipl_stat_col] if ipl_stat_col else 'N/A'

    pname = row.get('player_name', 'Player')
    rank  = row.get('rank', '?')
    score = row.get('RR_FIT_SCORE', 0)
    return (f"{pname} ranks #{rank} (score={score:.1f}). "
            f"Addresses RR's '{pw}' weakness. "
            f"RR stat: {rr_stat_val} vs IPL avg: {ipl_stat_val}. "
            f"Pressure score: {ps:.1f}.")

candidates['primary_reason'] = candidates.apply(build_primary_reason, axis=1)

# Output schema
output_cols = [
    'rank', 'player_id', 'player_name', 'determined_role',
    'nationality', 'age', 'availability_status',
    'RR_FIT_SCORE', 'pressure_score', 'weakness_fit_score',
    'reliability_norm', 'ipl_performance_score', 'recent_form_score',
    'venue_fit_score', 'upside_score', 'confidence_norm',
    'primary_weakness_addressed', 'primary_reason', 'risk_level',
    'rr_squad_2026', 'is_young', 'played_for_RR_ever',
    'first_ipl_season', 'seasons_in_ipl'
]

# Deduplicate column names if confidence_score or reliability_score already exist
if 'confidence_score' in candidates.columns and 'confidence_norm' in candidates.columns:
    candidates.drop(columns=['confidence_score'], inplace=True)
if 'reliability_score' in candidates.columns and 'reliability_norm' in candidates.columns:
    candidates.drop(columns=['reliability_score'], inplace=True)

# Rename for clean output
candidates.rename(columns={
    'reliability_norm': 'reliability_score',
    'confidence_norm': 'confidence_score',
}, inplace=True)

# Drop any duplicated column names in candidates
candidates = candidates.loc[:, ~candidates.columns.duplicated()].copy()

output_cols_renamed = [c.replace('reliability_norm', 'reliability_score').replace('confidence_norm', 'confidence_score')
                       for c in output_cols]
# Keep unique column order
seen = set()
output_cols_final = []
for c in output_cols_renamed:
    if c in candidates.columns and c not in seen:
        seen.add(c)
        output_cols_final.append(c)

rankings_df = candidates[output_cols_final].copy()

# Save main rankings
rankings_df.to_csv(os.path.join(OUT_DIR, 'rr_ipl2027_rankings.csv'), index=False)
print(f"  Saved rr_ipl2027_rankings.csv ({len(rankings_df):,} rows)")

# Top 10 summary
top10 = rankings_df.head(10).copy()
top10.to_csv(os.path.join(OUT_DIR, 'top10_summary.csv'), index=False)
print(f"  Saved top10_summary.csv")

# Young/uncapped targets
young_col = 'is_young' if 'is_young' in rankings_df.columns else None
if young_col:
    young_targets = candidates[candidates['is_young'] == True].sort_values('upside_score', ascending=False).head(50)
    young_out_cols = [c for c in output_cols_final if c in young_targets.columns]
    young_targets[young_out_cols].to_csv(os.path.join(OUT_DIR, 'young_uncapped_targets.csv'), index=False)
    print(f"  Saved young_uncapped_targets.csv ({len(young_targets)} rows)")

# Role-specific sub-rankings
BATTER_ROLES  = ['opener', 'top-order', 'middle-order', 'finisher', 'batter', 'batsman']
BOWLER_ROLES  = ['bowler', 'spinner']
AR_ROLES      = ['all-rounder', 'allrounder']
DEATH_BOWLER_ROLES = ['death bowler']
SPINNER_ROLES = ['spinner']
FINISHER_ROLES = ['finisher']


def role_filter(df, keywords):
    mask = df['determined_role'].str.lower().apply(
        lambda r: any(k in r for k in keywords) if pd.notna(r) else False
    )
    return df[mask].head(10)


role_subsets = {
    'top_batters_ranking':     role_filter(rankings_df, BATTER_ROLES),
    'top_bowlers_ranking':     role_filter(rankings_df, BOWLER_ROLES),
    'top_allrounders_ranking': role_filter(rankings_df, AR_ROLES),
    'top_death_bowlers':       role_filter(rankings_df, DEATH_BOWLER_ROLES),
    'top_spinners':            role_filter(rankings_df, SPINNER_ROLES),
    'top_finishers':           role_filter(rankings_df, FINISHER_ROLES),
}

for name, df_role in role_subsets.items():
    path = os.path.join(OUT_DIR, f'{name}.csv')
    df_role.to_csv(path, index=False)
    print(f"  Saved {name}.csv ({len(df_role)} rows)")

# ---------------------------------------------------------------------------
# SECTION 8 — NUMERICAL EXPLANATIONS (Phase 32)
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("SECTION 8 — Numerical Explanations (Phase 32)")
print("=" * 70)

# Top 10 detailed explanation
top10_detailed = top10.copy()
explanation_rows = []

# Get RR's primary weakness details
rr_primary_weakness = {}
if not rr_weak.empty:
    weak_cat_col  = next((c for c in ['weakness_category', 'category', 'metric'] if c in rr_weak.columns), None)
    weak_rr_col   = next((c for c in ['rr_value', 'rr_stat', 'rr_avg'] if c in rr_weak.columns), None)
    weak_ipl_col  = next((c for c in ['ipl_avg', 'ipl_benchmark', 'league_avg'] if c in rr_weak.columns), None)
    weak_score_col = next((c for c in ['weakness_score', 'score'] if c in rr_weak.columns), None)

    if weak_score_col:
        top_weak = rr_weak.sort_values(weak_score_col, ascending=False).iloc[0]
    else:
        top_weak = rr_weak.iloc[0]

    if weak_cat_col:
        rr_primary_weakness = {
            'category': top_weak[weak_cat_col] if weak_cat_col else 'N/A',
            'rr_value':  round(float(top_weak[weak_rr_col]), 2) if weak_rr_col and not pd.isna(top_weak[weak_rr_col]) else 'N/A',
            'ipl_avg':   round(float(top_weak[weak_ipl_col]), 2) if weak_ipl_col and not pd.isna(top_weak[weak_ipl_col]) else 'N/A',
        }

def safe_scalar(val, default=0.0):
    if isinstance(val, (pd.Series, np.ndarray, list)):
        val = val.iloc[0] if hasattr(val, 'iloc') else val[0]
    if pd.isna(val) or val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

for _, row in top10_detailed.iterrows():
    pname = str(row.get('player_name', 'Player'))
    if isinstance(pname, (pd.Series, np.ndarray, list)):
        pname = pname.iloc[0] if hasattr(pname, 'iloc') else pname[0]
    rank  = row.get('rank', '?')
    if isinstance(rank, (pd.Series, np.ndarray, list)):
        rank = rank.iloc[0] if hasattr(rank, 'iloc') else rank[0]
    pw    = rr_primary_weakness.get('category', row.get('primary_weakness_addressed', 'N/A'))
    if isinstance(pw, (pd.Series, np.ndarray, list)):
        pw = pw.iloc[0] if hasattr(pw, 'iloc') else pw[0]
    rr_stat_v = rr_primary_weakness.get('rr_value', 'N/A')
    ipl_avg_v = rr_primary_weakness.get('ipl_avg', 'N/A')

    # Player's relevant stat (for top weakness metric)
    player_stat_v = 'N/A'
    if overall_sr_col and overall_sr_col in row.index:
        val = row.get(overall_sr_col, np.nan)
        if isinstance(val, (pd.Series, np.ndarray, list)):
            val = val.iloc[0] if hasattr(val, 'iloc') else val[0]
        player_stat_v = round(float(val), 2) if not pd.isna(val) else 'N/A'

    pressure_stat = round(safe_scalar(row.get('pressure_score', 0)), 2)
    pressure_delta_raw = row.get('pressure_delta_SR', safe_scalar(row.get('pressure_score', 0)) - 50) if 'pressure_delta_SR' in row else safe_scalar(row.get('pressure_score', 0)) - 50
    pressure_delta_v = round(safe_scalar(pressure_delta_raw), 2)

    rel_score = round(safe_scalar(row.get('reliability_score', 50)) / 100, 3)
    fit_score = round(safe_scalar(row.get('RR_FIT_SCORE', 0)), 2)
    conf_score = round(safe_scalar(row.get('confidence_score', 50)) / 100, 3)

    exp = {
        'player': pname,
        'rank': rank,
        "RR's_largest_relevant_weakness": pw,
        'rr_stat': rr_stat_v,
        'ipl_benchmark': ipl_avg_v,
        'player_stat': player_stat_v,
        'player_pressure_stat': pressure_stat,
        'pressure_delta': pressure_delta_v,
        'reliability_score': rel_score,
        'rr_fit_score': fit_score,
        'confidence_score': conf_score,
        'reason': (
            f"{pname} ranks #{rank}. They directly address RR's '{pw}' weakness "
            f"where RR scores {rr_stat_v} vs IPL avg {ipl_avg_v}. "
            f"This player achieves {player_stat_v} with a pressure delta of {pressure_delta_v}."
        )
    }
    explanation_rows.append(exp)

# Add explanation columns to player_fit_scores.csv (for top 10)
explain_df = pd.DataFrame(explanation_rows)
explain_df.to_csv(os.path.join(OUT_DIR, 'top10_explanations.csv'), index=False)
print(f"  Saved top10_explanations.csv")

# Reload and update player_fit_scores with explanation columns
pfs = pd.read_csv(os.path.join(OUT_DIR, 'player_fit_scores.csv'))
if not explain_df.empty and 'player' in explain_df.columns:
    explain_merge = explain_df.rename(columns={'player': 'player_name'})
    for col in ['reason', 'RR\'s_largest_relevant_weakness', 'player_stat', 'pressure_delta']:
        if col in explain_merge.columns:
            pfs = pfs.merge(explain_merge[['player_name', col]].drop_duplicates('player_name'), on='player_name', how='left', suffixes=('', '_exp'))

pfs.to_csv(os.path.join(OUT_DIR, 'player_fit_scores.csv'), index=False)
print(f"  Updated player_fit_scores.csv with explanations ({len(pfs):,} rows)")

# ---------------------------------------------------------------------------
# FINAL SUMMARY
# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("PIPELINE P5 COMPLETE")
print("=" * 70)
print(f"  Outputs saved to: {OUT_DIR}")
print()
print("  WATCHLIST — Availability Requires Confirmation")
print("  All auction statuses are UNKNOWN. No official IPL 2027 data exists.")
print()
print(f"  Total players ranked: {len(rankings_df)}")
print(f"  Top 5 candidates:")
for _, row in rankings_df.head(5).iterrows():
    print(f"    #{int(row['rank'])}: {row['player_name']} | "
          f"Score={row['RR_FIT_SCORE']:.1f} | "
          f"Role={row.get('determined_role','?')} | "
          f"Risk={row['risk_level']}")
print()
print("  Files created:")
for f in [
    'player_fit_scores.csv', 'rr_ipl2027_rankings.csv', 'top10_summary.csv',
    'top10_explanations.csv', 'young_uncapped_targets.csv',
    'top_batters_ranking.csv', 'top_bowlers_ranking.csv', 'top_allrounders_ranking.csv',
    'top_death_bowlers.csv', 'top_spinners.csv', 'top_finishers.csv',
]:
    fpath = os.path.join(OUT_DIR, f)
    exists = "✓" if os.path.exists(fpath) else "✗"
    print(f"    {exists} {f}")
