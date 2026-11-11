"""
pipeline_p3_player_metrics.py
RR IPL 2027 Selection Pipeline — Phases 8–13
Player Metrics: Batting/Bowling Baselines, Role, Pressure Performance,
                Reliability, Confidence Scoring

Reads:
  results/pressure_features.csv
  6af3166e7b922_data_pack/playing_eleven.csv
  6af3166e7b922_data_pack/matches.csv
  6af3166e7b922_data_pack/competitions.csv
  6af3166e7b922_data_pack/competition_team_player_mapping.csv

Writes (to results/):
  player_batting_metrics.csv
  player_bowling_metrics.csv
  pressure_player_metrics.csv
  player_reliability.csv
  player_role_analysis.csv
"""

import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR = r"C:\Users\LOQ\Desktop\RR_IPL_Selection"
DATA_DIR = os.path.join(BASE_DIR, "6af3166e7b922_data_pack")
OUT_DIR  = os.path.join(BASE_DIR, "results")
os.makedirs(OUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
MIN_BALLS = 30  # minimum deliveries for a metric to be meaningful


def safe_div(num, den, fill=np.nan):
    """Element-wise safe division for scalars."""
    if den == 0 or den != den:  # nan check
        return fill
    return num / den


def safe_sr(runs, balls, min_balls=MIN_BALLS):
    if balls < min_balls:
        return np.nan
    return safe_div(runs, balls, np.nan) * 100


def safe_avg(runs, dismissals, min_balls=None, balls=0):
    if min_balls is not None and balls < min_balls:
        return np.nan
    if dismissals == 0:
        return 999.0
    return runs / dismissals


def normalize_0_1(val, lo, hi):
    """Clamp and normalize val to [0, 1] given [lo, hi] range."""
    if hi == lo:
        return 0.0
    return float(np.clip((val - lo) / (hi - lo), 0.0, 1.0))


def phase_economy(grp, phase):
    """Economy rate for a given innings_phase from a bowler group."""
    sub = grp[grp["innings_phase"] == phase]
    balls = sub["is_legal"].sum()
    runs  = sub["team_runs_ball"].sum()
    if balls < MIN_BALLS:
        return np.nan
    overs = balls / 6
    return safe_div(runs, overs, np.nan)


def phase_sr(grp, phase):
    """Strike rate for given innings_phase from batter group (legal only)."""
    sub = grp[grp["innings_phase"] == phase]
    balls = len(sub)
    runs  = sub["runs"].sum()
    if balls < MIN_BALLS:
        return np.nan
    return runs / balls * 100


# ─────────────────────────────────────────────
# SECTION 0 — LOAD & FILTER
# ─────────────────────────────────────────────
print("=" * 60)
print("SECTION 0 — Loading data …")
print("=" * 60)

bbb = pd.read_csv(os.path.join(OUT_DIR, "pressure_features.csv"), low_memory=False)
playing_eleven = pd.read_csv(os.path.join(DATA_DIR, "playing_eleven.csv"), low_memory=False)
matches        = pd.read_csv(os.path.join(DATA_DIR, "matches.csv"), low_memory=False)
competitions   = pd.read_csv(os.path.join(DATA_DIR, "competitions.csv"), low_memory=False)

# Optional file (may not exist in all data packs)
ctpm_path = os.path.join(DATA_DIR, "competition_team_player_mapping.csv")
if os.path.exists(ctpm_path):
    ctpm = pd.read_csv(ctpm_path, low_memory=False)
else:
    ctpm = pd.DataFrame()

print(f"  Loaded pressure_features.csv: {len(bbb):,} rows")

# ── Add season from competitions ──────────────────────────────────────────────
# competitions columns may be: id, name, season, competition_type (or similar)
comp_cols = competitions.columns.tolist()
print(f"  competitions columns: {comp_cols}")

season_col = None
for c in ["season", "year", "Season", "Year"]:
    if c in comp_cols:
        season_col = c
        break

comp_id_col = None
for c in ["id", "comp_id", "competition_id", "ID"]:
    if c in comp_cols:
        comp_id_col = c
        break

if season_col and comp_id_col:
    season_map = competitions.set_index(comp_id_col)[season_col].to_dict()
    bbb["season"] = bbb["comp_id"].map(season_map)
else:
    # Fallback: derive season from match_date year
    bbb["season"] = pd.to_datetime(bbb["match_date"], errors="coerce").dt.year
    print("  WARNING: could not find season col in competitions; using match year")

# ── Filter flags ──────────────────────────────────────────────────────────────
bbb["is_legal"] = bbb["is_legal"].astype(bool)
bbb["is_ipl"]   = bbb["is_ipl"].astype(bool)

ipl = bbb[bbb["is_ipl"]].copy()
ipl_legal = ipl[ipl["is_legal"]].copy()

print(f"  IPL rows total : {len(ipl):,}")
print(f"  IPL legal only : {len(ipl_legal):,}")

# ── Coerce numeric fields ─────────────────────────────────────────────────────
for col in ["runs", "is_four", "is_six", "is_wicket", "team_runs_ball",
            "batting_order", "pressure_index"]:
    if col in ipl_legal.columns:
        ipl_legal[col] = pd.to_numeric(ipl_legal[col], errors="coerce").fillna(0)
    if col in ipl.columns:
        ipl[col] = pd.to_numeric(ipl[col], errors="coerce").fillna(0)

ipl_legal["is_wicket"] = ipl_legal["is_wicket"].astype(int)
ipl["is_wicket"] = ipl["is_wicket"].astype(int)

# Ensure pressure_category is string
ipl_legal["pressure_category"] = ipl_legal["pressure_category"].astype(str)
ipl["pressure_category"]       = ipl["pressure_category"].astype(str)

# ── Identify batter dismissals ────────────────────────────────────────────────
# A batter is out if is_wicket == 1 AND the dismissal_type is not a wide-related
# and dismissed_player_id == striker_id OR dismissed_player_id is NaN (old data)
# Safest: exclude run-outs of non-striker
def compute_batter_out(df):
    """Return boolean Series: True if striker was dismissed on this delivery."""
    # dismissed_player_id matches striker_id (most cases)
    # OR dismissed_player_id is NaN (assume striker)
    # AND it is not "Run Out" of somebody else
    dismissed = pd.to_numeric(df["dismissed_player_id"], errors="coerce")
    striker   = pd.to_numeric(df["striker_id"], errors="coerce")
    is_wkt    = df["is_wicket"].astype(bool)

    # Non-striker run out: dismissed_player_id != striker_id AND dismissal_type == 'Run Out'
    runout_col = None
    for c in ["dismissal_type", "dismissal_type_id"]:
        if c in df.columns:
            runout_col = c
            break

    if runout_col and runout_col == "dismissal_type":
        non_striker_ro = (
            is_wkt &
            (df["dismissal_type"].str.lower().str.contains("run out", na=False)) &
            (dismissed != striker)
        )
    else:
        non_striker_ro = pd.Series(False, index=df.index)

    batter_out = is_wkt & ~non_striker_ro
    return batter_out.astype(int)

ipl_legal["batter_out"] = compute_batter_out(ipl_legal)

# ── Pressure categories ───────────────────────────────────────────────────────
PRESSURE_CATS = ["NORMAL", "MODERATE", "HIGH", "EXTREME"]
HIGH_EXT      = ["HIGH", "EXTREME"]


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — BATTING BASELINE METRICS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 1 — Batting baselines …")
print("=" * 60)

bat = ipl_legal.copy()


def batting_metrics_for_group(grp, min_b=MIN_BALLS):
    """Compute all batting metrics for a group of deliveries."""
    balls   = len(grp)
    runs    = grp["runs"].sum()
    fours   = grp["is_four"].sum()
    sixes   = grp["is_six"].sum()
    dismi   = grp["batter_out"].sum()
    dots    = (grp["runs"] == 0).sum()
    matches = grp["match_id"].nunique()
    innings = grp.groupby(["match_id", "innings"]).ngroups

    sr    = safe_sr(runs, balls, min_b)
    avg   = safe_avg(runs, dismi, min_b, balls) if balls >= min_b else np.nan
    bndry = (fours + sixes) / balls * 100 if balls >= min_b else np.nan
    dot_p = dots / balls * 100 if balls >= min_b else np.nan

    return {
        "matches"        : matches,
        "innings"        : innings,
        "balls_faced"    : balls,
        "runs"           : runs,
        "fours"          : fours,
        "sixes"          : sixes,
        "dismissals"     : dismi,
        "dot_balls"      : dots,
        "strike_rate"    : sr,
        "average"        : avg,
        "boundary_pct"   : bndry,
        "dot_ball_pct"   : dot_p,
    }


records = []

for (sid, sname), grp in bat.groupby(["striker_id", "striker_name"], sort=False):
    r = {"striker_id": sid, "striker_name": sname}

    # ── Overall ───────────────────────────────────────────────────────────────
    overall = batting_metrics_for_group(grp)
    r.update(overall)

    # ── Phase splits ──────────────────────────────────────────────────────────
    for phase in ["POWERPLAY", "MIDDLE", "DEATH"]:
        pkey = phase.lower() + "_SR"
        r[pkey] = phase_sr(grp, phase)

    # ── Bowling type matchup ──────────────────────────────────────────────────
    if "pace_or_spin" in grp.columns:
        pace_vals = grp["pace_or_spin"].dropna().unique()
        pace_kws  = [v for v in pace_vals if "pace" in str(v).lower() or "fast" in str(v).lower()]
        spin_kws  = [v for v in pace_vals if "spin" in str(v).lower()]

        g_pace = grp[grp["pace_or_spin"].isin(pace_kws)]
        g_spin = grp[grp["pace_or_spin"].isin(spin_kws)]

        r["SR_vs_pace"] = phase_sr(g_pace, None) if len(g_pace) >= MIN_BALLS else np.nan
        r["SR_vs_spin"] = phase_sr(g_spin, None) if len(g_spin) >= MIN_BALLS else np.nan

        # Inline SR for all innings_phases combined
        def _sr_all(sub):
            b = len(sub); ru = sub["runs"].sum()
            return ru / b * 100 if b >= MIN_BALLS else np.nan
        r["SR_vs_pace"] = _sr_all(g_pace)
        r["SR_vs_spin"] = _sr_all(g_spin)
    else:
        r["SR_vs_pace"] = np.nan
        r["SR_vs_spin"] = np.nan

    # ── Bowling arm matchup ───────────────────────────────────────────────────
    if "bowling_type" in grp.columns:
        bt = grp["bowling_type"].fillna("")
        g_left  = grp[bt.str.contains("left|Left", na=False)]
        g_right = grp[bt.str.contains("right|Right", na=False)]

        def _sr_all(sub):
            b = len(sub); ru = sub["runs"].sum()
            return ru / b * 100 if b >= MIN_BALLS else np.nan

        r["SR_vs_left_arm"]  = _sr_all(g_left)
        r["SR_vs_right_arm"] = _sr_all(g_right)
    else:
        r["SR_vs_left_arm"]  = np.nan
        r["SR_vs_right_arm"] = np.nan

    # ── Situation metrics ─────────────────────────────────────────────────────
    def _sr_cond(sub):
        b = len(sub); ru = sub["runs"].sum()
        return ru / b * 100 if b >= MIN_BALLS else np.nan

    r["chasing_SR"]   = _sr_cond(grp[grp["innings"] == 2])
    r["defending_SR"] = _sr_cond(grp[grp["innings"] == 1])

    if "required_run_rate" in grp.columns and "balls_remaining" in grp.columns:
        high_rrr = grp[(grp["required_run_rate"] > 10) & (grp["innings"] == 2)]
        close    = grp[
            (grp["innings"] == 2) &
            ((grp["runs_required"] - grp["balls_remaining"]).abs() < 15)
        ] if "runs_required" in grp.columns else pd.DataFrame()
    else:
        high_rrr = pd.DataFrame()
        close    = pd.DataFrame()

    r["high_RRR_SR"]   = _sr_cond(high_rrr)
    r["close_match_SR"] = _sr_cond(close)

    if "wickets_last_6_balls" in grp.columns:
        post_wkt = grp[grp["wickets_last_6_balls"] >= 1]
        r["post_wicket_SR"] = _sr_cond(post_wkt)
    else:
        r["post_wicket_SR"] = np.nan

    # ── Pressure splits ───────────────────────────────────────────────────────
    for cat in PRESSURE_CATS:
        sub = grp[grp["pressure_category"] == cat]
        b   = len(sub)
        ru  = sub["runs"].sum()
        di  = sub["batter_out"].sum()
        r[f"pressure_balls_{cat}"]  = b
        r[f"pressure_SR_{cat}"]     = ru / b * 100 if b >= MIN_BALLS else np.nan
        r[f"pressure_avg_{cat}"]    = safe_avg(ru, di, MIN_BALLS, b)

    # ── Season tracking ───────────────────────────────────────────────────────
    r["seasons"] = grp["season"].nunique() if "season" in grp.columns else 0

    records.append(r)

batting_df = pd.DataFrame(records)
print(f"  Batting metrics computed for {len(batting_df):,} batters")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — BOWLING BASELINE METRICS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 2 — Bowling baselines …")
print("=" * 60)

# Use all IPL deliveries for bowling (legal for counting balls; all for runs)
bowl_all   = ipl.copy()
bowl_legal = ipl_legal.copy()

bowl_records = []

bowler_ids = ipl.groupby(["bowler_id", "bowler_name"]).ngroups
print(f"  Processing {bowler_ids:,} bowlers …")

for (bid, bname), grp_all in ipl.groupby(["bowler_id", "bowler_name"], sort=False):
    grp_legal = grp_all[grp_all["is_legal"]]

    r = {"bowler_id": bid, "bowler_name": bname}

    balls   = len(grp_legal)
    overs   = balls / 6 if balls > 0 else 0
    runs_c  = grp_all["team_runs_ball"].sum()
    wickets = grp_legal["is_wicket"].sum()
    dot_b   = ((grp_legal["team_runs_ball"] == 0)).sum()
    bounds  = (grp_legal["is_four"] | grp_legal["is_six"]).sum()

    r["balls_bowled"]     = balls
    r["overs"]            = round(overs, 2)
    r["runs_conceded"]    = runs_c
    r["wickets"]          = wickets
    r["economy"]          = safe_div(runs_c, overs, np.nan) if overs > 0 else np.nan
    r["bowling_average"]  = safe_div(runs_c, wickets, 999.0) if wickets > 0 else 999.0
    r["bowling_SR"]       = safe_div(balls, wickets, 999.0)  if wickets > 0 else 999.0
    r["dot_ball_pct"]     = dot_b / balls * 100 if balls >= MIN_BALLS else np.nan
    r["boundary_pct_bow"] = bounds / balls * 100 if balls >= MIN_BALLS else np.nan

    # Phase splits (economy)
    for phase in ["POWERPLAY", "MIDDLE", "DEATH"]:
        r[f"{phase.lower()}_economy"] = phase_economy(grp_all, phase)

    # Matchup by batting hand
    if "batting_type" in grp_legal.columns:
        bt = grp_legal["batting_type"].fillna("")
        g_lhb = grp_legal[bt.str.contains("LHB|Left|left", na=False)]
        g_rhb = grp_legal[bt.str.contains("RHB|Right|right", na=False)]

        def _eco(sub):
            b = len(sub); ru = sub["team_runs_ball"].sum()
            ov = b / 6
            return safe_div(ru, ov, np.nan) if b >= MIN_BALLS else np.nan

        r["economy_vs_LHB"] = _eco(g_lhb)
        r["economy_vs_RHB"] = _eco(g_rhb)
    else:
        r["economy_vs_LHB"] = np.nan
        r["economy_vs_RHB"] = np.nan

    # Pressure situations (economy)
    def _eco_grp(sub):
        b  = len(sub[sub["is_legal"]])
        ru = sub["team_runs_ball"].sum()
        ov = b / 6
        return safe_div(ru, ov, np.nan) if b >= MIN_BALLS else np.nan

    if "required_run_rate" in grp_all.columns:
        high_rrr_grp = grp_all[
            (grp_all["required_run_rate"] > 10) & (grp_all["innings"] == 2)
        ]
    else:
        high_rrr_grp = pd.DataFrame(columns=grp_all.columns)

    # Also include high pressure_index
    if "pressure_index" in grp_all.columns:
        pi_high = grp_all[grp_all["pressure_index"] > 60]
        if len(high_rrr_grp) == 0:
            high_rrr_grp = pi_high
        else:
            high_rrr_grp = pd.concat([high_rrr_grp, pi_high]).drop_duplicates()

    r["high_RRR_economy"] = _eco_grp(high_rrr_grp)

    close_match = grp_all[grp_all["pressure_category"].isin(["HIGH", "EXTREME"])]
    r["close_match_economy"] = _eco_grp(close_match)

    death_pres = grp_all[
        (grp_all["innings_phase"] == "DEATH") &
        (grp_all["pressure_category"].isin(["HIGH", "EXTREME"]))
    ]
    r["death_pressure_economy"] = _eco_grp(death_pres)

    # Pressure splits
    for cat in PRESSURE_CATS:
        sub_all   = grp_all[grp_all["pressure_category"] == cat]
        sub_legal = sub_all[sub_all["is_legal"]]
        b   = len(sub_legal)
        ov  = b / 6
        ru  = sub_all["team_runs_ball"].sum()
        wk  = sub_legal["is_wicket"].sum()
        eco = safe_div(ru, ov, np.nan) if b >= MIN_BALLS else np.nan
        wkr = safe_div(wk, ov, np.nan) if b >= MIN_BALLS else np.nan

        r[f"bowler_pressure_balls_{cat}"]    = b
        r[f"bowler_economy_{cat}"]           = eco
        r[f"bowler_wicket_rate_{cat}"]       = wkr

    r["matches_bowled"] = grp_all["match_id"].nunique()
    r["seasons"]        = grp_all["season"].nunique() if "season" in grp_all.columns else 0

    bowl_records.append(r)

bowling_df = pd.DataFrame(bowl_records)
print(f"  Bowling metrics computed for {len(bowling_df):,} bowlers")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — ROLE DETERMINATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 3 — Role determination …")
print("=" * 60)

# Average batting order
avg_batting_order = (
    ipl_legal.groupby("striker_id")["batting_order"]
    .mean()
    .rename("avg_batting_order")
)

# WK flag from playing_eleven
pe_cols = playing_eleven.columns.tolist()
print(f"  playing_eleven columns: {pe_cols}")

wk_col = None
pid_col = None
for c in ["is_wk", "isWK", "is_wicketkeeper", "wk"]:
    if c in pe_cols:
        wk_col = c
        break
for c in ["player_id", "playerId", "id"]:
    if c in pe_cols:
        pid_col = c
        break

if wk_col and pid_col:
    wk_map = (
        playing_eleven.groupby(pid_col)[wk_col]
        .any()
        .astype(bool)
        .to_dict()
    )
else:
    wk_map = {}
    print("  WARNING: WK flag could not be determined from playing_eleven columns")

# Dominant bowl type (Spin vs Pace) per bowler
if "pace_or_spin" in ipl_legal.columns:
    bowl_type_dom = (
        ipl_legal.groupby("bowler_id")["pace_or_spin"]
        .agg(lambda x: x.mode().iloc[0] if len(x) > 0 else "Unknown")
        .rename("dominant_bowl_type")
    )
else:
    bowl_type_dom = pd.Series(dtype=str, name="dominant_bowl_type")

# Collect all player ids (union of batters and bowlers)
all_player_ids = set(batting_df["striker_id"]).union(set(bowling_df["bowler_id"]))

role_records = []

for pid in all_player_ids:
    bat_row  = batting_df[batting_df["striker_id"] == pid]
    bowl_row = bowling_df[bowling_df["bowler_id"]  == pid]

    has_bat  = len(bat_row) > 0
    has_bowl = len(bowl_row) > 0

    # Player name
    if has_bat:
        pname = bat_row.iloc[0]["striker_name"]
    elif has_bowl:
        pname = bowl_row.iloc[0]["bowler_name"]
    else:
        pname = "Unknown"

    balls_faced  = int(bat_row.iloc[0]["balls_faced"])  if has_bat  else 0
    balls_bowled = int(bowl_row.iloc[0]["balls_bowled"]) if has_bowl else 0

    avg_bo = float(avg_batting_order.get(pid, 7.0))

    # Dominant bowl type
    dom_bowl = str(bowl_type_dom.get(pid, "Unknown"))

    # Phase economies for bowlers
    if has_bowl:
        pp_eco   = bowl_row.iloc[0].get("powerplay_economy", np.nan)
        mid_eco  = bowl_row.iloc[0].get("middle_economy",    np.nan)
        dth_eco  = bowl_row.iloc[0].get("death_economy",     np.nan)
    else:
        pp_eco = mid_eco = dth_eco = np.nan

    # Role logic
    if balls_bowled >= 60 and balls_faced >= 60:
        if avg_bo <= 6:
            role = "Batting all-rounder"
        else:
            role = "Bowling all-rounder"
    elif balls_bowled >= 60:
        is_pace = "pace" in dom_bowl.lower() or "fast" in dom_bowl.lower()
        if is_pace:
            # determine best phase by lowest economy
            eco_map = {
                "powerplay": pp_eco if not np.isnan(pp_eco) else 999,
                "middle"   : mid_eco if not np.isnan(mid_eco) else 999,
                "death"    : dth_eco if not np.isnan(dth_eco) else 999,
            }
            best = min(eco_map, key=eco_map.get)
            if best == "death":
                role = "Death bowler"
            elif best == "powerplay":
                role = "Powerplay bowler"
            else:
                role = "Middle-over bowler"
        else:
            role = "Spinner"
    elif balls_faced >= 60:
        if avg_bo <= 2:
            role = "Opener"
        elif avg_bo <= 4:
            role = "Top-order batter"
        elif avg_bo <= 6:
            role = "Middle-order batter"
        elif avg_bo <= 8:
            role = "Finisher"
        else:
            role = "Lower-order batter"
    else:
        role = "Insufficient data"

    # WK prefix
    is_wk = wk_map.get(pid, False)
    if is_wk and any(role.startswith(x) for x in [
        "Opener", "Top-order", "Middle-order", "Finisher", "Lower-order"
    ]):
        role = "WK-" + role

    overall_sr  = float(bat_row.iloc[0]["strike_rate"])  if has_bat  else np.nan
    overall_avg = float(bat_row.iloc[0]["average"])      if has_bat  else np.nan
    overall_eco = float(bowl_row.iloc[0]["economy"])     if has_bowl else np.nan

    role_records.append({
        "player_id"    : pid,
        "player_name"  : pname,
        "primary_role" : role,
        "is_wk"        : is_wk,
        "balls_faced"  : balls_faced,
        "balls_bowled" : balls_bowled,
        "avg_batting_order": avg_bo,
        "dominant_bowl_type": dom_bowl,
        "overall_SR"   : overall_sr,
        "overall_avg"  : overall_avg,
        "overall_eco"  : overall_eco,
    })

role_df = pd.DataFrame(role_records)
print(f"  Role assigned for {len(role_df):,} players")
print("\n  Role distribution:")
print(role_df["primary_role"].value_counts().to_string())


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — PRESSURE PERFORMANCE METRICS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 4 — Pressure performance metrics …")
print("=" * 60)

pressure_records = []

# ── BATTING pressure metrics ──────────────────────────────────────────────────
for (sid, sname), grp in bat.groupby(["striker_id", "striker_name"], sort=False):
    r = {"player_id": sid, "player_name": sname, "player_type": "batter"}

    normal_grp  = grp[grp["pressure_category"] == "NORMAL"]
    high_ext_grp = grp[grp["pressure_category"].isin(HIGH_EXT)]
    extreme_grp  = grp[grp["pressure_category"] == "EXTREME"]

    def _sr(sub): 
        b = len(sub); ru = sub["runs"].sum()
        return ru / b * 100 if b >= MIN_BALLS else np.nan

    def _avg(sub):
        b = len(sub); ru = sub["runs"].sum(); di = sub["batter_out"].sum()
        if b < MIN_BALLS: return np.nan
        return safe_avg(ru, di)

    def _bndry(sub):
        b = len(sub)
        if b < MIN_BALLS: return np.nan
        return (sub["is_four"].sum() + sub["is_six"].sum()) / b * 100

    def _dismiss_rate(sub):
        b = len(sub); di = sub["batter_out"].sum()
        return di / b * 100 if b >= MIN_BALLS else np.nan

    normal_sr  = _sr(normal_grp)
    pressure_sr = _sr(high_ext_grp)
    r["normal_SR"]              = normal_sr
    r["pressure_SR"]            = pressure_sr
    r["pressure_SR_extreme"]    = _sr(extreme_grp)
    r["normal_avg"]             = _avg(normal_grp)
    r["pressure_avg"]           = _avg(high_ext_grp)
    r["normal_boundary_rate"]   = _bndry(normal_grp)
    r["pressure_boundary_rate"] = _bndry(high_ext_grp)
    r["normal_dismissal_rate"]  = _dismiss_rate(normal_grp)
    r["pressure_dismissal_rate"]= _dismiss_rate(high_ext_grp)

    # Delta: positive = clutch performer
    if not np.isnan(pressure_sr) and not np.isnan(normal_sr):
        r["pressure_delta_SR"] = pressure_sr - normal_sr
    else:
        r["pressure_delta_SR"] = np.nan

    # Pressure balls count
    r["pressure_balls"] = len(high_ext_grp)
    r["normal_balls"]   = len(normal_grp)

    # Pressure innings
    if len(high_ext_grp) > 0:
        r["pressure_innings"] = high_ext_grp.groupby(["match_id", "innings"]).ngroups
    else:
        r["pressure_innings"] = 0

    pressure_records.append(r)

# ── BOWLING pressure metrics ──────────────────────────────────────────────────
for (bid, bname), grp_all in ipl.groupby(["bowler_id", "bowler_name"], sort=False):
    r = {"player_id": bid, "player_name": bname, "player_type": "bowler"}

    normal_grp   = grp_all[grp_all["pressure_category"] == "NORMAL"]
    high_ext_grp = grp_all[grp_all["pressure_category"].isin(HIGH_EXT)]

    def _eco_sub(sub):
        b  = len(sub[sub["is_legal"]])
        ru = sub["team_runs_ball"].sum()
        ov = b / 6
        return safe_div(ru, ov, np.nan) if b >= MIN_BALLS else np.nan

    def _wkr_sub(sub):
        b  = len(sub[sub["is_legal"]])
        wk = sub[sub["is_legal"]]["is_wicket"].sum()
        ov = b / 6
        return safe_div(wk, ov, np.nan) if b >= MIN_BALLS else np.nan

    def _dot_rate(sub):
        sub_l = sub[sub["is_legal"]]
        b = len(sub_l)
        dots = (sub_l["team_runs_ball"] == 0).sum()
        return dots / b * 100 if b >= MIN_BALLS else np.nan

    normal_eco   = _eco_sub(normal_grp)
    pressure_eco = _eco_sub(high_ext_grp)
    r["normal_economy"]       = normal_eco
    r["pressure_economy"]     = pressure_eco
    r["normal_wicket_rate"]   = _wkr_sub(normal_grp)
    r["pressure_wicket_rate"] = _wkr_sub(high_ext_grp)
    r["normal_dot_rate"]      = _dot_rate(normal_grp)
    r["pressure_dot_rate"]    = _dot_rate(high_ext_grp)

    if not np.isnan(pressure_eco) and not np.isnan(normal_eco):
        r["pressure_delta_economy"] = pressure_eco - normal_eco
    else:
        r["pressure_delta_economy"] = np.nan

    r["pressure_balls"]   = len(high_ext_grp[high_ext_grp["is_legal"]])
    r["normal_balls"]     = len(normal_grp[normal_grp["is_legal"]])
    r["pressure_innings"] = (
        high_ext_grp.groupby(["match_id", "innings"]).ngroups
        if len(high_ext_grp) > 0 else 0
    )

    pressure_records.append(r)

pressure_df = pd.DataFrame(pressure_records)
print(f"  Pressure metrics for {len(pressure_df):,} records ({pressure_df['player_type'].value_counts().to_dict()})")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — RELIABILITY SCORING
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 5 — Reliability scoring …")
print("=" * 60)

reliability_records = []

# ── Batting reliability ───────────────────────────────────────────────────────
for (sid, sname), grp in bat.groupby(["striker_id", "striker_name"], sort=False):
    r = {"player_id": sid, "player_name": sname}

    # Per-match aggregation
    match_stats = []
    for mid, mgrp in grp.groupby("match_id"):
        mb  = len(mgrp)
        mru = mgrp["runs"].sum()
        msr = mru / mb * 100 if mb >= 6 else np.nan
        # Pressure SR in this match
        pres_grp = mgrp[mgrp["pressure_category"].isin(HIGH_EXT)]
        pb = len(pres_grp)
        psr = pres_grp["runs"].sum() / pb * 100 if pb >= 1 else np.nan
        match_stats.append({"match_sr": msr, "pressure_sr": psr, "balls": mb})

    ms_df = pd.DataFrame(match_stats)
    valid = ms_df.dropna(subset=["match_sr"])

    if len(valid) == 0:
        r.update({
            "mtm_SR_variance": np.nan,
            "season_SR_variance": np.nan,
            "median_match_SR": np.nan,
            "pressure_matches_above_baseline": np.nan,
            "reliability_score_bat": np.nan,
        })
        reliability_records.append(r)
        continue

    mtm_var = valid["match_sr"].std()
    med_sr  = valid["match_sr"].median()

    # Season variance
    if "season" in grp.columns:
        season_sr = grp.groupby("season").apply(
            lambda sg: sg["runs"].sum() / len(sg) * 100 if len(sg) >= 6 else np.nan
        ).dropna()
        ssn_var = season_sr.std() if len(season_sr) > 1 else 0.0
    else:
        ssn_var = 0.0

    # Overall SR
    overall_sr = grp["runs"].sum() / len(grp) * 100

    # Pressure matches above baseline
    pres_valid = ms_df.dropna(subset=["pressure_sr"])
    if len(pres_valid) > 0:
        above = (pres_valid["pressure_sr"] >= overall_sr).mean()
    else:
        above = 0.5  # neutral

    score = 100 * (
        0.30 * (1 - normalize_0_1(mtm_var, 0, 50)) +
        0.30 * normalize_0_1(above, 0, 1) +
        0.20 * normalize_0_1(med_sr / 150, 0, 1) +
        0.20 * (1 - normalize_0_1(ssn_var, 0, 30))
    )
    score = float(np.clip(score, 0, 100))

    r.update({
        "mtm_SR_variance"               : mtm_var,
        "season_SR_variance"            : ssn_var,
        "median_match_SR"               : med_sr,
        "pressure_matches_above_baseline": above,
        "reliability_score_bat"         : score,
        "player_type"                   : "batter",
    })
    reliability_records.append(r)

# ── Bowling reliability ───────────────────────────────────────────────────────
for (bid, bname), grp_all in ipl.groupby(["bowler_id", "bowler_name"], sort=False):
    r = {"player_id": bid, "player_name": bname}

    match_stats = []
    for mid, mgrp in grp_all.groupby("match_id"):
        mgrp_l = mgrp[mgrp["is_legal"]]
        mb     = len(mgrp_l)
        mru    = mgrp["team_runs_ball"].sum()
        mov    = mb / 6
        meco   = mru / mov if mov > 0 else np.nan
        mwk    = mgrp_l["is_wicket"].sum()
        match_stats.append({"match_eco": meco, "match_wk": mwk, "balls": mb})

    ms_df = pd.DataFrame(match_stats)
    valid = ms_df.dropna(subset=["match_eco"])

    if len(valid) == 0:
        r.update({
            "mtm_eco_variance": np.nan,
            "season_eco_variance": np.nan,
            "median_match_eco": np.nan,
            "reliability_score_bowl": np.nan,
            "player_type": "bowler",
        })
        reliability_records.append(r)
        continue

    mtm_var = valid["match_eco"].std()
    med_eco = valid["match_eco"].median()

    if "season" in grp_all.columns:
        def _season_eco(sg):
            sl = sg[sg["is_legal"]]
            b = len(sl)
            if b < 6: return np.nan
            return sg["team_runs_ball"].sum() / (b / 6)
        season_eco = grp_all.groupby("season").apply(_season_eco).dropna()
        ssn_var    = season_eco.std() if len(season_eco) > 1 else 0.0
    else:
        ssn_var = 0.0

    # Lower economy is better → flip direction
    # Good: low variance, low economy
    score = 100 * (
        0.30 * (1 - normalize_0_1(mtm_var, 0, 4)) +   # low variance = consistent
        0.30 * (1 - normalize_0_1(med_eco, 4, 14)) +  # lower eco = better
        0.20 * normalize_0_1(valid["match_wk"].mean(), 0, 3) +  # wickets per match
        0.20 * (1 - normalize_0_1(ssn_var, 0, 3))
    )
    score = float(np.clip(score, 0, 100))

    r.update({
        "mtm_eco_variance"  : mtm_var,
        "season_eco_variance": ssn_var,
        "median_match_eco"  : med_eco,
        "reliability_score_bowl": score,
        "player_type"       : "bowler",
    })
    reliability_records.append(r)

reliability_df = pd.DataFrame(reliability_records)
print(f"  Reliability computed for {len(reliability_df):,} records")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — CONFIDENCE SCORING (Bayesian shrinkage)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 6 — Confidence scoring (Bayesian shrinkage) …")
print("=" * 60)

K_BAT  = 150
K_BOWL = 100
FULL_BAT_BALLS  = 300
FULL_BOWL_BALLS = 300

# Global mean SR across all IPL batters (min 60 balls)
bat_eligible = batting_df[batting_df["balls_faced"] >= 60]
global_mean_sr = (
    bat_eligible["runs"].sum() / bat_eligible["balls_faced"].sum() * 100
    if len(bat_eligible) > 0 else 125.0
)
print(f"  Global mean SR (IPL, ≥60 balls): {global_mean_sr:.2f}")

# Global mean economy for bowlers (min 60 balls)
bowl_eligible = bowling_df[bowling_df["balls_bowled"] >= 60]
global_mean_eco = bowl_eligible["economy"].dropna().mean() if len(bowl_eligible) > 0 else 8.0
print(f"  Global mean economy (IPL, ≥60 balls): {global_mean_eco:.2f}")

# ── Augment batting_df ────────────────────────────────────────────────────────
def apply_bat_shrinkage(row):
    bf  = row["balls_faced"]
    sr  = row["strike_rate"]
    sf  = bf / (bf + K_BAT)
    adj = sf * sr + (1 - sf) * global_mean_sr if not np.isnan(sr) else global_mean_sr
    conf = float(np.clip(bf / FULL_BAT_BALLS, 0, 1)) * 100
    return pd.Series({"shrinkage_factor_bat": sf, "adjusted_SR": adj, "confidence_score": conf})

bat_shrinkage = batting_df.apply(apply_bat_shrinkage, axis=1)
batting_df = pd.concat([batting_df, bat_shrinkage], axis=1)

# Pressure SR shrinkage (merge from pressure_df)
pres_bat = pressure_df[pressure_df["player_type"] == "batter"][
    ["player_id", "normal_SR", "pressure_SR", "pressure_balls"]
].copy()
pres_bat = pres_bat.rename(columns={"player_id": "striker_id"})
batting_df = batting_df.merge(pres_bat, on="striker_id", how="left",
                               suffixes=("", "_pres"))

def apply_pressure_shrinkage(row):
    pb  = row.get("pressure_balls", 0) or 0
    psr = row.get("pressure_SR", np.nan)
    nsr = row.get("normal_SR", np.nan)
    if np.isnan(psr) or np.isnan(nsr):
        return pd.Series({"shrinkage_factor_pressure": np.nan, "adjusted_pressure_SR": np.nan})
    sf  = pb / (pb + 60)
    adj = sf * psr + (1 - sf) * nsr
    return pd.Series({"shrinkage_factor_pressure": sf, "adjusted_pressure_SR": adj})

pres_shrink = batting_df.apply(apply_pressure_shrinkage, axis=1)
batting_df = pd.concat([batting_df, pres_shrink], axis=1)

# ── Augment bowling_df ────────────────────────────────────────────────────────
def apply_bowl_shrinkage(row):
    bb  = row["balls_bowled"]
    eco = row["economy"]
    sf  = bb / (bb + K_BOWL)
    adj = sf * eco + (1 - sf) * global_mean_eco if not np.isnan(eco) else global_mean_eco
    conf = float(np.clip(bb / FULL_BOWL_BALLS, 0, 1)) * 100
    return pd.Series({"shrinkage_factor_bowl": sf, "adjusted_economy": adj, "confidence_score_bowl": conf})

bowl_shrinkage = bowling_df.apply(apply_bowl_shrinkage, axis=1)
bowling_df = pd.concat([bowling_df, bowl_shrinkage], axis=1)

# ── Merge pressure and reliability into pressure_df ───────────────────────────
# Add adjusted metrics to pressure_df
pres_bat_adj = batting_df[["striker_id", "adjusted_SR", "adjusted_pressure_SR",
                            "confidence_score", "shrinkage_factor_bat"]].copy()
pres_bat_adj = pres_bat_adj.rename(columns={"striker_id": "player_id"})
pressure_df = pressure_df.merge(pres_bat_adj, on="player_id", how="left")

pres_bowl_adj = bowling_df[["bowler_id", "adjusted_economy",
                             "confidence_score_bowl", "shrinkage_factor_bowl"]].copy()
pres_bowl_adj = pres_bowl_adj.rename(columns={"bowler_id": "player_id"})
pressure_df = pressure_df.merge(pres_bowl_adj, on="player_id", how="left",
                                suffixes=("", "_bowl"))

print("  Confidence scores applied to batting and bowling DataFrames")

conf_bins = pd.cut(batting_df["confidence_score"].dropna(),
                   bins=[0, 20, 40, 60, 80, 100], include_lowest=True)
print("\n  Batting confidence score distribution:")
print(conf_bins.value_counts().sort_index().to_string())


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — SAMPLE SIZE TRACKING (already embedded, final pass)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 7 — Sample size tracking …")
print("=" * 60)

# Add pressure_innings to batting_df
pres_innings_bat = (
    bat[bat["pressure_category"].isin(HIGH_EXT)]
    .groupby("striker_id")
    .apply(lambda g: g.groupby(["match_id", "innings"]).ngroups)
    .rename("pressure_innings")
)
batting_df["pressure_innings"] = batting_df["striker_id"].map(pres_innings_bat).fillna(0).astype(int)

# pressure_deliveries_bowled
pres_del_bowl = (
    ipl[ipl["pressure_category"].isin(HIGH_EXT) & ipl["is_legal"]]
    .groupby("bowler_id")
    .size()
    .rename("pressure_deliveries_bowled")
)
bowling_df["pressure_deliveries_bowled"] = bowling_df["bowler_id"].map(pres_del_bowl).fillna(0).astype(int)

print("  Sample size columns confirmed in batting and bowling DataFrames")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — OUTPUTS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SECTION 8 — Saving output files …")
print("=" * 60)

batting_path  = os.path.join(OUT_DIR, "player_batting_metrics.csv")
bowling_path  = os.path.join(OUT_DIR, "player_bowling_metrics.csv")
pressure_path = os.path.join(OUT_DIR, "pressure_player_metrics.csv")
rel_path      = os.path.join(OUT_DIR, "player_reliability.csv")
role_path     = os.path.join(OUT_DIR, "player_role_analysis.csv")

batting_df.to_csv(batting_path,  index=False)
bowling_df.to_csv(bowling_path,  index=False)
pressure_df.to_csv(pressure_path, index=False)
reliability_df.to_csv(rel_path,  index=False)
role_df.to_csv(role_path,        index=False)

print(f"  ✓ {batting_path}")
print(f"  ✓ {bowling_path}")
print(f"  ✓ {pressure_path}")
print(f"  ✓ {rel_path}")
print(f"  ✓ {role_path}")


# ── Summary Prints ────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

n_batters = batting_df["striker_id"].nunique()
n_bowlers = bowling_df["bowler_id"].nunique()
print(f"\n  Total unique batters : {n_batters:,}")
print(f"  Total unique bowlers : {n_bowlers:,}")

print("\n  Role distribution:")
print(role_df["primary_role"].value_counts().to_string())

# Top 10 by pressure SR (min 60 pressure balls, batters only)
pres_bat_view = pressure_df[
    (pressure_df["player_type"] == "batter") &
    (pressure_df["pressure_balls"] >= 60) &
    (pressure_df["pressure_SR"].notna())
].nlargest(10, "pressure_SR")[["player_name", "pressure_SR", "pressure_balls",
                                "normal_SR", "pressure_delta_SR"]]
print("\n  Top 10 IPL batters by pressure_SR (min 60 pressure balls):")
print(pres_bat_view.to_string(index=False))

# Top 10 bowlers by pressure economy (min 30 pressure balls) — lowest is best
pres_bowl_view = pressure_df[
    (pressure_df["player_type"] == "bowler") &
    (pressure_df["pressure_balls"] >= 30) &
    (pressure_df["pressure_economy"].notna())
].nsmallest(10, "pressure_economy")[["player_name", "pressure_economy", "pressure_balls",
                                      "normal_economy", "pressure_delta_economy"]]
print("\n  Top 10 IPL bowlers by pressure_economy (min 30 pressure balls, lowest = best):")
print(pres_bowl_view.to_string(index=False))

print("\n  Batting confidence score distribution:")
print(conf_bins.value_counts().sort_index().to_string())

print("\n✅ pipeline_p3_player_metrics.py completed successfully.")
