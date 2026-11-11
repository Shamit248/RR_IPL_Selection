"""
pipeline_p4_model_rr_weakness.py
RR IPL 2027 Selection Pipeline — Phases 14–19

Phases:
  14 — Model Training (time-aware, 4 variants A/B/C/D)
  15 — Model Validation
  16–17 — RR IPL 2026 Weakness Analysis vs IPL benchmark
  18 — Weakness Scoring
  19 — Required Player Profiles

Reads  (from results/):
  pressure_features.csv
  player_batting_metrics.csv
  player_bowling_metrics.csv
  pressure_player_metrics.csv
  player_reliability.csv
  rr_ipl_2026_matches.csv

Writes (to results/):
  model_validation.csv
  model_comparison.csv
  rr_batting_analysis.csv
  rr_bowling_analysis.csv
  rr_weaknesses.csv
  rr_required_player_profiles.csv
"""

import os, warnings, time
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings('ignore')

DATA = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\6af3166e7b922_data_pack'
OUT  = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\results'
os.makedirs(OUT, exist_ok=True)

RR_TEAM_ID = 3
IPL_COMP_IDS = {1358, 1715, 2193, 2725, 3298}

t0 = time.time()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 0 — LOAD DATA
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 70)
print("SECTION 0 — Loading data")
print("=" * 70)

def load_or_warn(path, name):
    if os.path.exists(path):
        df = pd.read_csv(path, low_memory=False)
        print(f"  Loaded {name}: {len(df):,} rows")
        return df
    else:
        print(f"  WARNING: {name} not found at {path}")
        return pd.DataFrame()

pf   = load_or_warn(f'{OUT}/pressure_features.csv', 'pressure_features')
bat  = load_or_warn(f'{OUT}/player_batting_metrics.csv', 'player_batting_metrics')
bowl = load_or_warn(f'{OUT}/player_bowling_metrics.csv', 'player_bowling_metrics')
ppm  = load_or_warn(f'{OUT}/pressure_player_metrics.csv', 'pressure_player_metrics')
rel  = load_or_warn(f'{OUT}/player_reliability.csv', 'player_reliability')
rr26 = load_or_warn(f'{OUT}/rr_ipl_2026_matches.csv', 'rr_ipl_2026_matches')

# Type coercions
pf['is_ipl']   = pf['is_ipl'].astype(bool)
pf['is_legal'] = pf['is_legal'].astype(bool)
pf['season']   = pf['season'].astype(str).str[:4]

ipl     = pf[pf['is_ipl']].copy()
ipl_leg = ipl[ipl['is_legal']].copy()

print(f"  IPL total:  {len(ipl):,}")
print(f"  IPL legal:  {len(ipl_leg):,}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — PRESSURE MODEL TRAINING (Phases 14–15)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 1 — Model Training (Phases 14–15)")
print("=" * 70)

model_results = []

# Try importing sklearn/xgboost
try:
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, roc_auc_score
    from sklearn.preprocessing import StandardScaler
    SKLEARN_OK = True
    print("  sklearn available")
except ImportError:
    SKLEARN_OK = False
    print("  WARNING: sklearn not available — skipping ML models")

try:
    import xgboost as xgb
    XGB_OK = True
    print("  xgboost available")
except ImportError:
    XGB_OK = False
    print("  xgboost not available — using GradientBoosting instead")

try:
    import shap
    SHAP_OK = True
except ImportError:
    SHAP_OK = False

# Build player-match level dataset for modelling
# Target: match-level pressure_SR for each batter
# Features: various player/match context stats

if SKLEARN_OK and not bat.empty and not ppm.empty and not rel.empty:
    print("\n  Building player-season modelling dataset...")

    # Merge batting + pressure + reliability on striker_id
    bat_id = 'striker_id'   # batting metrics use striker_id
    ppm_id = 'player_id'    # pressure metrics use player_id
    rel_id = 'player_id'    # reliability uses player_id

    # Rename bat's striker_id to player_id for uniform merging
    merged = bat.copy()
    merged['player_id'] = merged[bat_id]

    if not ppm.empty:
        # Only keep batting rows from ppm
        ppm_bat = ppm[ppm['player_type'] == 'batter'].copy() if 'player_type' in ppm.columns else ppm.copy()
        ppm_cols = [ppm_id] + [c for c in ppm_bat.columns if c not in merged.columns and c != 'player_name']
        merged = merged.merge(ppm_bat[ppm_cols], on=ppm_id, how='left')
    if not rel.empty:
        rel_bat = rel[rel['player_type'] == 'batter'].copy() if 'player_type' in rel.columns else rel.copy()
        rel_cols = [rel_id] + [c for c in rel_bat.columns if c not in merged.columns and c != 'player_name']
        merged = merged.merge(rel_bat[rel_cols], on=rel_id, how='left')

    print(f"  Merged player dataset: {len(merged)} players, {len(merged.columns)} cols")

    # Define feature sets for 4 models
    # Model A — normal stats only
    feat_A = [c for c in ['strike_rate','average','boundary_pct','dot_ball_pct',
                           'balls_faced','matches'] if c in merged.columns]

    # Model B — normal + pressure
    feat_B = feat_A + [c for c in ['pressure_SR','pressure_avg','pressure_delta_SR',
                                    'pressure_balls'] if c in merged.columns]

    # Model C — normal + pressure + consistency
    feat_C = feat_B + [c for c in ['reliability_score_bat','confidence_score',
                                    'match_to_match_variance'] if c in merged.columns]

    # Model D — full model
    feat_D = feat_C + [c for c in ['powerplay_SR','middle_SR','death_SR',
                                    'SR_vs_pace','SR_vs_spin'] if c in merged.columns]

    # Target: adjusted_pressure_SR if available, else pressure_SR
    target_col = None
    for tc in ['adjusted_pressure_SR','pressure_SR','pressure_SR_HIGH']:
        if tc in merged.columns:
            target_col = tc
            break

    if target_col is None:
        print("  No pressure SR target column found — skipping model training")
        model_rows = []
    else:
        print(f"  Target column: {target_col}")

        # Need season for time-aware split
        # Add season from first_ipl_season or manually
        # Use merge from competition mapping
        ctpm = pd.read_csv(f'{DATA}/competition_team_player_mapping.csv', low_memory=False)
        comp = pd.read_csv(f'{DATA}/competitions.csv', low_memory=False)
        ipl_comps = comp[comp['comp_name'].str.contains('IPL', case=False, na=False)]
        ipl_comps['season_yr'] = ipl_comps['season'].astype(str).str[:4].astype(int)

        ctpm_ipl = ctpm[ctpm['comp_id'].isin(IPL_COMP_IDS)].copy()
        ctpm_ipl = ctpm_ipl.merge(ipl_comps[['comp_id','season_yr']], on='comp_id', how='left')
        player_first_season = ctpm_ipl.groupby('player_id')['season_yr'].min().reset_index()
        player_first_season.columns = ['player_id','first_ipl_season']

        pid_col = bat_id
        if pid_col in merged.columns:
            merged = merged.merge(player_first_season, left_on=pid_col, right_on='player_id', how='left')

        # Time-aware folds using 'first_ipl_season' as a proxy for the player's main era
        # This is imperfect but avoids random splits
        # We'll use season-aware split from ipl_leg data instead

        # Build delivery-level player-season data for time splits
        # Aggregate by player × season
        ipl_leg_copy = ipl_leg.copy()
        ipl_leg_copy['season'] = ipl_leg_copy['season'].astype(str).str[:4]

        def player_season_stats(df):
            g = df.groupby(['striker_id','season'])
            out = []
            for (sid, seas), grp in g:
                balls = len(grp)
                if balls < 30:
                    continue
                runs = grp['runs'].sum()
                dismi = grp['is_wicket'].sum()
                SR = runs / balls * 100
                hep_grp = grp[grp['pressure_category'].isin(['HIGH','EXTREME'])]
                p_balls = len(hep_grp)
                p_runs  = hep_grp['runs'].sum()
                p_SR = p_runs / p_balls * 100 if p_balls >= 15 else np.nan
                out.append({
                    'striker_id': sid, 'season': seas,
                    'balls': balls, 'runs': runs, 'SR': SR,
                    'dismissals': dismi,
                    'pressure_balls': p_balls, 'pressure_SR': p_SR,
                    'boundary_pct': (grp['is_four'].sum() + grp['is_six'].sum()) / balls * 100,
                    'dot_pct': (grp['runs'] == 0).sum() / balls * 100,
                })
            return pd.DataFrame(out)

        ps = player_season_stats(ipl_leg_copy)
        ps = ps.dropna(subset=['pressure_SR'])
        print(f"  Player-season records (min 30 balls): {len(ps)}")

        model_rows = []

        # Validation folds
        folds = [
            ('2022-2024', {'2022','2023','2024'}, {'2025'}),
            ('2022-2025', {'2022','2023','2024','2025'}, {'2026'}),
        ]

        for fold_name, train_seasons, val_seasons in folds:
            train = ps[ps['season'].isin(train_seasons)]
            val   = ps[ps['season'].isin(val_seasons)]
            if len(train) < 20 or len(val) < 10:
                print(f"  Fold {fold_name}: insufficient data (train={len(train)}, val={len(val)})")
                continue

            print(f"\n  Fold {fold_name}: train={len(train)}, val={len(val)}")

            feat_map = {
                'A': ['SR','boundary_pct','dot_pct','balls'],
                'B': ['SR','boundary_pct','dot_pct','balls','pressure_SR'],
                'C': ['SR','boundary_pct','dot_pct','balls','pressure_SR','pressure_balls'],
                'D': ['SR','boundary_pct','dot_pct','balls','pressure_SR','pressure_balls','dismissals'],
            }

            for model_name, feats in feat_map.items():
                feats = [f for f in feats if f in train.columns]
                if not feats:
                    continue
                X_tr = train[feats].fillna(train[feats].mean())
                y_tr = train['pressure_SR']
                X_val = val[feats].fillna(train[feats].mean())
                y_val = val['pressure_SR']

                try:
                    if XGB_OK:
                        mdl = xgb.XGBRegressor(n_estimators=100, max_depth=4,
                                               learning_rate=0.1, random_state=42,
                                               verbosity=0)
                    else:
                        mdl = GradientBoostingRegressor(n_estimators=100, max_depth=4,
                                                        learning_rate=0.1, random_state=42)

                    mdl.fit(X_tr, y_tr)
                    preds = mdl.predict(X_val)

                    mae  = mean_absolute_error(y_val, preds)
                    rmse = np.sqrt(mean_squared_error(y_val, preds))
                    r2   = r2_score(y_val, preds)
                    rho, pval = stats.spearmanr(y_val, preds)

                    # Top-20 precision: how many of predicted top-20 are actual top-20
                    if len(y_val) >= 20:
                        actual_top20  = set(y_val.nlargest(20).index)
                        pred_top20    = set(pd.Series(preds, index=y_val.index).nlargest(20).index)
                        top20_prec    = len(actual_top20 & pred_top20) / 20
                    else:
                        top20_prec = np.nan

                    row = {
                        'model': model_name,
                        'fold': fold_name,
                        'train_n': len(train),
                        'val_n': len(val),
                        'mae': round(mae, 3),
                        'rmse': round(rmse, 3),
                        'r2': round(r2, 3),
                        'spearman_rho': round(rho, 3),
                        'top20_precision': round(top20_prec, 3) if not np.isnan(top20_prec) else np.nan,
                        'features_used': len(feats),
                    }
                    model_rows.append(row)
                    print(f"    Model {model_name}: MAE={mae:.2f} RMSE={rmse:.2f} R²={r2:.3f} ρ={rho:.3f} top20={top20_prec:.2f}")
                except Exception as e:
                    print(f"    Model {model_name} failed: {e}")

        # Save model comparison
        if model_rows:
            mc = pd.DataFrame(model_rows)
            mc.to_csv(f'{OUT}/model_comparison.csv', index=False)
            print(f"\n  Saved model_comparison.csv ({len(mc)} rows)")

            # Determine best model
            best = mc.sort_values('spearman_rho', ascending=False).iloc[0]
            print(f"  Best model: {best['model']} (fold {best['fold']}, ρ={best['spearman_rho']:.3f})")

            # Does pressure data help? Compare A vs B
            a_rho = mc[mc['model']=='A']['spearman_rho'].mean()
            b_rho = mc[mc['model']=='B']['spearman_rho'].mean()
            print(f"\n  Pressure improvement (B vs A): {b_rho:.3f} vs {a_rho:.3f} "
                  f"({'YES' if b_rho > a_rho else 'NO'})")
        else:
            pd.DataFrame().to_csv(f'{OUT}/model_comparison.csv', index=False)

        # Save model_validation (player-level predictions)
        # Use best available model on full dataset
        if model_rows:
            best_feats_key = model_rows[-1]['model']
            feats_full = [f for f in feat_map.get(best_feats_key, ['SR']) if f in ps.columns]
            X_full = ps[feats_full].fillna(ps[feats_full].mean())
            if XGB_OK:
                final_mdl = xgb.XGBRegressor(n_estimators=100, max_depth=4,
                                              learning_rate=0.1, random_state=42, verbosity=0)
            else:
                final_mdl = GradientBoostingRegressor(n_estimators=100, max_depth=4,
                                                      learning_rate=0.1, random_state=42)
            final_mdl.fit(X_full.fillna(0), ps['pressure_SR'])
            ps['predicted_pressure_SR'] = final_mdl.predict(X_full.fillna(0))
            ps.to_csv(f'{OUT}/model_validation.csv', index=False)
            print(f"  Saved model_validation.csv ({len(ps)} rows)")

            if SHAP_OK:
                try:
                    explainer = shap.TreeExplainer(final_mdl)
                    shap_vals = explainer.shap_values(X_full.fillna(0))
                    shap_df = pd.DataFrame(shap_vals, columns=feats_full)
                    shap_means = shap_df.abs().mean().sort_values(ascending=False)
                    print("\n  SHAP feature importance:")
                    print(shap_means.to_string())
                except Exception as e:
                    print(f"  SHAP failed: {e}")
        else:
            ps.to_csv(f'{OUT}/model_validation.csv', index=False)

else:
    print("  Skipping ML — missing sklearn or player metrics not ready")
    pd.DataFrame().to_csv(f'{OUT}/model_comparison.csv', index=False)
    pd.DataFrame().to_csv(f'{OUT}/model_validation.csv', index=False)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — RR IPL 2026 WEAKNESS ANALYSIS (Phases 16–17)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 2 — RR IPL 2026 Weakness Analysis")
print("=" * 70)

if rr26.empty:
    print("  ERROR: rr_ipl_2026_matches.csv not found — cannot proceed")
else:
    # RR match IDs
    rr_match_ids = set(rr26['match_id'].unique())
    print(f"  RR IPL 2026 match_ids: {len(rr_match_ids)}")

    # IPL 2026 deliveries
    ipl_2026 = ipl_leg[ipl_leg['comp_id'] == 3298].copy()
    rr_all   = ipl_leg[ipl_leg['match_id'].isin(rr_match_ids)].copy()

    print(f"  IPL 2026 legal deliveries: {len(ipl_2026):,}")
    print(f"  RR match deliveries: {len(rr_all):,}")

    # RR batting = batting_team_id == 3
    rr_bat = rr_all[rr_all['batting_team_id'] == RR_TEAM_ID].copy()
    # RR bowling = bowling_team_id == 3
    rr_bowl = rr_all[rr_all['bowling_team_id'] == RR_TEAM_ID].copy()

    # IPL 2026 batting/bowling (all teams including RR — for league avg)
    ipl26_bat  = ipl_2026.copy()
    ipl26_bowl = ipl_2026.copy()

    print(f"  RR batting deliveries: {len(rr_bat):,}")
    print(f"  RR bowling deliveries: {len(rr_bowl):,}")

    # ── Helper functions ──────────────────────────────────────────────────────
    def batting_stats(df, label='', min_balls=20):
        """Compute batting stats from delivery-level data."""
        balls = len(df)
        if balls < min_balls:
            return {'label': label, 'balls': balls,
                    'SR': np.nan, 'boundary_pct': np.nan, 'dot_pct': np.nan,
                    'avg': np.nan, 'wkts_per_100': np.nan}
        runs  = df['runs'].sum()
        wkts  = df['is_wicket'].sum()
        fours = df['is_four'].sum()
        sixes = df['is_six'].sum()
        dots  = (df['runs'] == 0).sum()
        return {
            'label': label,
            'balls': balls,
            'SR':           round(runs / balls * 100, 2),
            'avg':          round(runs / max(wkts, 1), 2),
            'boundary_pct': round((fours + sixes) / balls * 100, 2),
            'dot_pct':      round(dots / balls * 100, 2),
            'wkts_per_100': round(wkts / balls * 100, 3),
        }

    def bowling_stats(df, label='', min_balls=20):
        """Compute bowling stats from delivery-level data."""
        balls = len(df)
        if balls < min_balls:
            return {'label': label, 'balls': balls,
                    'economy': np.nan, 'wkts_per_over': np.nan,
                    'dot_pct': np.nan, 'boundary_pct': np.nan}
        overs = balls / 6
        runs  = df['team_runs_ball'].sum()
        wkts  = df['is_wicket'].sum()
        fours = df['is_four'].sum()
        sixes = df['is_six'].sum()
        dots  = (df['team_runs_ball'] == 0).sum()
        return {
            'label': label,
            'balls': balls,
            'economy':       round(runs / overs, 2),
            'wkts_per_over': round(wkts / overs, 2),
            'dot_pct':       round(dots / balls * 100, 2),
            'boundary_pct':  round((fours + sixes) / balls * 100, 2),
        }

    # ── BATTING ANALYSIS ──────────────────────────────────────────────────────
    print("\n  Computing RR batting analysis...")
    bat_rows = []

    def add_bat(rr_df, ipl_df, cat_name, min_balls=20):
        rr_s  = batting_stats(rr_df,  label=f'RR {cat_name}',  min_balls=min_balls)
        ipl_s = batting_stats(ipl_df, label=f'IPL {cat_name}', min_balls=min_balls)
        for metric in ['SR','avg','boundary_pct','dot_pct','wkts_per_100']:
            rr_val  = rr_s.get(metric, np.nan)
            ipl_val = ipl_s.get(metric, np.nan)
            gap = round(rr_val - ipl_val, 2) if (not np.isnan(rr_val) and not np.isnan(ipl_val)) else np.nan
            gap_pct = round(gap / abs(ipl_val) * 100, 1) if (gap is not np.nan and ipl_val and ipl_val != 0) else np.nan
            bat_rows.append({
                'category': cat_name,
                'metric': metric,
                'rr_value': rr_val,
                'ipl_avg': ipl_val,
                'gap': gap,
                'gap_pct': gap_pct,
                'rr_balls': rr_s['balls'],
                'ipl_balls': ipl_s['balls'],
            })

    # 1. Overall
    add_bat(rr_bat, ipl26_bat, 'Overall')

    # 2. Phase
    for phase in ['POWERPLAY','MIDDLE','DEATH']:
        add_bat(rr_bat[rr_bat['innings_phase']==phase],
                ipl26_bat[ipl26_bat['innings_phase']==phase], f'Phase_{phase}')

    # 3. vs Pace / Spin
    for ps_type in ipl_leg['pace_or_spin'].dropna().unique() if 'pace_or_spin' in ipl_leg.columns else []:
        add_bat(rr_bat[rr_bat['pace_or_spin']==ps_type],
                ipl26_bat[ipl26_bat['pace_or_spin']==ps_type], f'vs_{ps_type}')

    # 4. Chasing (innings 2) / Defending (innings 1)
    add_bat(rr_bat[rr_bat['innings']==2], ipl26_bat[ipl26_bat['innings']==2], 'Chasing')
    add_bat(rr_bat[rr_bat['innings']==1], ipl26_bat[ipl26_bat['innings']==1], 'Defending')

    # 5. Pressure situations
    add_bat(rr_bat[rr_bat['pressure_category'].isin(['HIGH','EXTREME'])],
            ipl26_bat[ipl26_bat['pressure_category'].isin(['HIGH','EXTREME'])],
            'Pressure_HIGH_EXTREME', min_balls=15)

    # 6. High RRR (>10, innings 2)
    high_rrr_rr  = rr_bat[(rr_bat['innings']==2) & (rr_bat['required_run_rate'] > 10)]
    high_rrr_ipl = ipl26_bat[(ipl26_bat['innings']==2) & (ipl26_bat['required_run_rate'] > 10)]
    add_bat(high_rrr_rr, high_rrr_ipl, 'High_RRR', min_balls=10)

    # 7. After wicket (recent wicket in last 6 balls)
    add_bat(rr_bat[rr_bat['wickets_last_6_balls'] >= 1],
            ipl26_bat[ipl26_bat['wickets_last_6_balls'] >= 1], 'Post_Wicket', min_balls=10)

    # 8. Close matches (abs(runs_required - balls_remaining) < 15 in innings 2)
    if 'runs_required' in rr_bat.columns and 'balls_remaining' in rr_bat.columns:
        close_rr = rr_bat[(rr_bat['innings']==2) &
                          (abs(rr_bat['runs_required'] - rr_bat['balls_remaining']) < 15)]
        close_ipl = ipl26_bat[(ipl26_bat['innings']==2) &
                               (abs(ipl26_bat['runs_required'] - ipl26_bat['balls_remaining']) < 15)]
        add_bat(close_rr, close_ipl, 'Close_Match', min_balls=5)

    # 9. vs Left/Right arm bowling
    if 'bowling_type' in rr_bat.columns:
        left_arm_rr  = rr_bat[rr_bat['bowling_type'].str.contains('Left', case=False, na=False)]
        right_arm_rr = rr_bat[rr_bat['bowling_type'].str.contains('Right', case=False, na=False)]
        left_arm_ipl = ipl26_bat[ipl26_bat['bowling_type'].str.contains('Left', case=False, na=False)]
        right_arm_ipl = ipl26_bat[ipl26_bat['bowling_type'].str.contains('Right', case=False, na=False)]
        add_bat(left_arm_rr, left_arm_ipl, 'vs_LeftArm')
        add_bat(right_arm_rr, right_arm_ipl, 'vs_RightArm')

    rr_bat_df = pd.DataFrame(bat_rows)
    rr_bat_df.to_csv(f'{OUT}/rr_batting_analysis.csv', index=False)
    print(f"  Saved rr_batting_analysis.csv ({len(rr_bat_df)} rows)")

    # ── BOWLING ANALYSIS ──────────────────────────────────────────────────────
    print("\n  Computing RR bowling analysis...")
    bowl_rows = []

    def add_bowl(rr_df, ipl_df, cat_name, min_balls=20):
        rr_s  = bowling_stats(rr_df,  label=f'RR {cat_name}',  min_balls=min_balls)
        ipl_s = bowling_stats(ipl_df, label=f'IPL {cat_name}', min_balls=min_balls)
        for metric in ['economy','wkts_per_over','dot_pct','boundary_pct']:
            rr_val  = rr_s.get(metric, np.nan)
            ipl_val = ipl_s.get(metric, np.nan)
            gap = round(rr_val - ipl_val, 2) if (not np.isnan(rr_val) and not np.isnan(ipl_val)) else np.nan
            gap_pct = round(gap / abs(ipl_val) * 100, 1) if (gap is not np.nan and ipl_val and ipl_val != 0) else np.nan
            bowl_rows.append({
                'category': cat_name,
                'metric': metric,
                'rr_value': rr_val,
                'ipl_avg': ipl_val,
                'gap': gap,
                'gap_pct': gap_pct,
                'rr_balls': rr_s['balls'],
                'ipl_balls': ipl_s['balls'],
            })

    # 1. Overall
    add_bowl(rr_bowl, ipl26_bowl, 'Overall')

    # 2. Phase
    for phase in ['POWERPLAY','MIDDLE','DEATH']:
        add_bowl(rr_bowl[rr_bowl['innings_phase']==phase],
                 ipl26_bowl[ipl26_bowl['innings_phase']==phase], f'Phase_{phase}')

    # 3. vs LHB / RHB
    if 'batting_type' in rr_bowl.columns:
        for bt in ipl_leg['batting_type'].dropna().unique() if 'batting_type' in ipl_leg.columns else []:
            add_bowl(rr_bowl[rr_bowl['batting_type']==bt],
                     ipl26_bowl[ipl26_bowl['batting_type']==bt], f'vs_{bt}')

    # 4. Pressure
    add_bowl(rr_bowl[rr_bowl['pressure_category'].isin(['HIGH','EXTREME'])],
             ipl26_bowl[ipl26_bowl['pressure_category'].isin(['HIGH','EXTREME'])],
             'Pressure_HIGH_EXTREME', min_balls=15)

    # 5. High RRR bowling (opponent chasing >10 RRR)
    rr_bowl_hrr  = rr_bowl[(rr_bowl['innings']==2) & (rr_bowl['required_run_rate'] > 10)]
    ipl_bowl_hrr = ipl26_bowl[(ipl26_bowl['innings']==2) & (ipl26_bowl['required_run_rate'] > 10)]
    add_bowl(rr_bowl_hrr, ipl_bowl_hrr, 'HighRRR_Bowling', min_balls=10)

    # 6. Death close matches
    death_rr  = rr_bowl[rr_bowl['innings_phase']=='DEATH']
    death_ipl = ipl26_bowl[ipl26_bowl['innings_phase']=='DEATH']
    if len(death_rr) >= 15:
        add_bowl(death_rr[death_rr['pressure_category'].isin(['HIGH','EXTREME'])],
                 death_ipl[death_ipl['pressure_category'].isin(['HIGH','EXTREME'])],
                 'Death_Pressure', min_balls=10)

    rr_bowl_df = pd.DataFrame(bowl_rows)
    rr_bowl_df.to_csv(f'{OUT}/rr_bowling_analysis.csv', index=False)
    print(f"  Saved rr_bowling_analysis.csv ({len(rr_bowl_df)} rows)")

    # ── Print key RR stats ─────────────────────────────────────────────────────
    print("\n  KEY RR IPL 2026 BATTING METRICS:")
    key_bat = rr_bat_df[rr_bat_df['metric']=='SR'].sort_values('rr_value')
    for _, row in key_bat.iterrows():
        print(f"    {row['category']:30s}: RR={row['rr_value']:.1f}  IPL={row['ipl_avg']:.1f}  "
              f"gap={row['gap']:+.1f}  balls={row['rr_balls']}")

    print("\n  KEY RR IPL 2026 BOWLING METRICS (Economy):")
    key_bowl = rr_bowl_df[rr_bowl_df['metric']=='economy'].sort_values('rr_value', ascending=False)
    for _, row in key_bowl.iterrows():
        print(f"    {row['category']:30s}: RR={row['rr_value']:.2f}  IPL={row['ipl_avg']:.2f}  "
              f"gap={row['gap']:+.2f}  balls={row['rr_balls']}")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — WEAKNESS SCORING (Phase 18)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 3 — Weakness Scoring")
print("=" * 70)

weakness_rows = []

def add_weakness(category, weakness_type, metric, rr_val, ipl_val, balls,
                 tactical_imp, is_bad_when_positive=True):
    """
    For batting: gap = rr_val - ipl_val; negative gap is a weakness (SR too low)
    For bowling economy: positive gap is a weakness (economy too high)
    is_bad_when_positive: True if higher value = bad (economy), False if lower = bad (SR)
    """
    if np.isnan(rr_val) or np.isnan(ipl_val) or balls < 10:
        return
    gap = rr_val - ipl_val
    # Weakness magnitude: how bad is it?
    if is_bad_when_positive:
        weakness_magnitude = max(0, gap)   # bowling economy: higher = worse
    else:
        weakness_magnitude = max(0, -gap)  # batting SR: lower = worse (gap negative = problem)

    if weakness_magnitude == 0:
        return  # not a weakness, skip

    gap_pct = abs(gap) / abs(ipl_val) * 100 if ipl_val != 0 else 0

    # Normalize gap to 0–1 (use 20% as rough max)
    gap_norm  = min(1.0, gap_pct / 25.0)
    ball_norm = min(1.0, balls / 500.0)
    tac_norm  = tactical_imp  # already 0–1

    # Confidence: more balls = higher confidence
    conf = min(1.0, balls / 300.0)

    weakness_score = (
        0.40 * gap_norm +
        0.25 * tac_norm +
        0.20 * conf     +
        0.15 * ball_norm
    )
    severity = ('CRITICAL' if weakness_score >= 0.6 else
                'SIGNIFICANT' if weakness_score >= 0.4 else
                'MODERATE' if weakness_score >= 0.2 else 'MINOR')

    weakness_rows.append({
        'weakness_type':   weakness_type,
        'category':        category,
        'metric':          metric,
        'rr_value':        round(rr_val, 2),
        'ipl_avg':         round(ipl_val, 2),
        'gap':             round(gap, 2),
        'gap_pct':         round(gap_pct, 1),
        'balls_sample':    balls,
        'tactical_importance': tactical_imp,
        'weakness_score':  round(weakness_score, 3),
        'severity':        severity,
    })

if not rr26.empty:
    # From batting analysis
    for _, row in rr_bat_df.iterrows():
        cat = row['category']
        metric = row['metric']
        rr_val = row['rr_value']
        ipl_val = row['ipl_avg']
        balls = row['rr_balls']

        if np.isnan(rr_val) or np.isnan(ipl_val):
            continue

        # Tactical importance
        tac = {'DEATH': 1.0, 'POWERPLAY': 0.8, 'MIDDLE': 0.85,
               'Overall': 0.7, 'Pressure': 0.9, 'Close': 0.9,
               'High_RRR': 0.95, 'Chasing': 0.8}.get(
            next((k for k in ['DEATH','POWERPLAY','MIDDLE','Overall','Pressure','Close','High_RRR','Chasing']
                  if k in cat), ''), 0.6)

        # For batting: SR, boundary_pct → lower than IPL = bad
        if metric in ['SR','boundary_pct']:
            add_weakness(cat, 'batting', metric, rr_val, ipl_val, balls, tac,
                         is_bad_when_positive=False)
        # dot_pct: higher than IPL = bad
        elif metric == 'dot_pct':
            add_weakness(cat, 'batting', metric, rr_val, ipl_val, balls, tac,
                         is_bad_when_positive=True)

    # From bowling analysis
    for _, row in rr_bowl_df.iterrows():
        cat = row['category']
        metric = row['metric']
        rr_val = row['rr_value']
        ipl_val = row['ipl_avg']
        balls = row['rr_balls']

        if np.isnan(rr_val) or np.isnan(ipl_val):
            continue

        tac = {'DEATH': 1.0, 'POWERPLAY': 0.8, 'MIDDLE': 0.85,
               'Pressure': 0.9, 'Death_Pressure': 1.0}.get(
            next((k for k in ['DEATH','POWERPLAY','MIDDLE','Pressure','Death_Pressure']
                  if k in cat), ''), 0.65)

        # Economy: higher = bad for bowler
        if metric == 'economy':
            add_weakness(cat, 'bowling', metric, rr_val, ipl_val, balls, tac,
                         is_bad_when_positive=True)
        # wkts_per_over: lower = bad
        elif metric == 'wkts_per_over':
            add_weakness(cat, 'bowling', metric, rr_val, ipl_val, balls, tac,
                         is_bad_when_positive=False)
        # boundary_pct given: higher = bad
        elif metric == 'boundary_pct':
            add_weakness(cat, 'bowling', metric, rr_val, ipl_val, balls, tac,
                         is_bad_when_positive=True)

    if weakness_rows:
        wk_df = pd.DataFrame(weakness_rows)
        wk_df = wk_df.sort_values('weakness_score', ascending=False).reset_index(drop=True)
        wk_df.insert(0, 'rank', wk_df.index + 1)
        wk_df.to_csv(f'{OUT}/rr_weaknesses.csv', index=False)
        print(f"  Saved rr_weaknesses.csv ({len(wk_df)} weaknesses found)")

        print("\n  TOP 10 RR WEAKNESSES:")
        for _, row in wk_df.head(10).iterrows():
            print(f"  [{row['rank']:2d}] {row['weakness_type']:10s} | {row['category']:30s} | "
                  f"{row['metric']:15s} | RR={row['rr_value']:.2f} IPL={row['ipl_avg']:.2f} "
                  f"gap={row['gap']:+.2f} | {row['severity']}")
    else:
        print("  No weaknesses found (all metrics at or above IPL average)")
        pd.DataFrame().to_csv(f'{OUT}/rr_weaknesses.csv', index=False)
        wk_df = pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — REQUIRED PLAYER PROFILES (Phase 19)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SECTION 4 — Required Player Profiles")
print("=" * 70)

profiles = []

if 'wk_df' in dir() and not wk_df.empty:
    # Group by category to find top distinct weaknesses (not just metrics of same situation)
    top_cats = wk_df.drop_duplicates(subset=['category','weakness_type']).head(10)

    role_map = {
        'batting': {
            'POWERPLAY':   ['Opener', 'Top-order batter'],
            'MIDDLE':      ['Middle-order batter', 'Batting all-rounder'],
            'DEATH':       ['Finisher', 'Middle-order batter'],
            'Overall':     ['Top-order batter', 'Middle-order batter'],
            'Chasing':     ['Middle-order batter', 'Finisher'],
            'High_RRR':    ['Finisher', 'Middle-order batter'],
            'Pressure':    ['Middle-order batter', 'Finisher'],
            'Post_Wicket': ['Middle-order batter', 'Finisher'],
            'Close_Match': ['Middle-order batter', 'Finisher'],
        },
        'bowling': {
            'POWERPLAY':          ['Powerplay bowler', 'Fast bowler'],
            'MIDDLE':             ['Middle-over bowler', 'Spinner', 'Bowling all-rounder'],
            'DEATH':              ['Death bowler', 'Fast bowler'],
            'Pressure':           ['Death bowler', 'Middle-over bowler'],
            'Death_Pressure':     ['Death bowler', 'Fast bowler'],
            'HighRRR_Bowling':    ['Death bowler', 'Fast bowler'],
        }
    }

    primary_metric_map = {
        ('batting','SR'):           ('strike_rate', '>= IPL avg + gap'),
        ('batting','boundary_pct'): ('boundary_pct', '>= IPL avg + gap'),
        ('batting','dot_pct'):      ('dot_pct',      '<= IPL avg'),
        ('bowling','economy'):      ('economy',      '<= IPL avg - gap'),
        ('bowling','wkts_per_over'):('wkts_per_over','>=  IPL avg'),
        ('bowling','boundary_pct'): ('boundary_pct', '<= IPL avg'),
    }

    for idx, row in top_cats.iterrows():
        cat  = row['category']
        wtype = row['weakness_type']
        metric = row['metric']
        rr_val = row['rr_value']
        ipl_val = row['ipl_avg']

        # Phase extraction
        phase = next((p for p in ['POWERPLAY','MIDDLE','DEATH'] if p in cat), None)
        ptype = next((p for p in ['Pace','Spin','Left','Right'] if p.lower() in cat.lower()), None)
        situation = next((s for s in ['Chasing','Pressure','High_RRR','Post_Wicket','Close_Match']
                         if s in cat), None)

        # Roles
        roles = []
        if wtype == 'batting' and phase:
            roles = role_map['batting'].get(phase, ['Middle-order batter'])
        elif wtype == 'batting' and situation:
            roles = role_map['batting'].get(situation, ['Middle-order batter'])
        elif wtype == 'batting':
            roles = role_map['batting'].get('Overall', ['Middle-order batter'])
        elif wtype == 'bowling' and phase:
            roles = role_map['bowling'].get(phase, ['Middle-over bowler'])
        elif wtype == 'bowling' and situation:
            roles = role_map['bowling'].get(situation, ['Death bowler'])
        elif wtype == 'bowling':
            roles = role_map['bowling'].get('Overall', ['Middle-over bowler'])

        pm_key = (wtype, metric)
        prim_metric, prim_threshold = primary_metric_map.get(pm_key, (metric, f'>= {ipl_val:.1f}'))

        # Threshold: player must beat IPL average (since RR is below it)
        if wtype == 'batting' and metric in ['SR','boundary_pct']:
            threshold = f'>= {ipl_val:.1f}'
        elif wtype == 'batting' and metric == 'dot_pct':
            threshold = f'<= {ipl_val:.1f}'
        elif wtype == 'bowling' and metric == 'economy':
            threshold = f'<= {ipl_val:.2f}'
        elif wtype == 'bowling' and metric == 'wkts_per_over':
            threshold = f'>= {ipl_val:.2f}'
        else:
            threshold = f'better than {ipl_val:.2f}'

        profile = {
            'weakness_rank':          row['rank'],
            'weakness_category':      cat,
            'weakness_type':          wtype,
            'weakness_metric':        metric,
            'rr_value':               rr_val,
            'ipl_avg':                ipl_val,
            'gap':                    row['gap'],
            'severity':               row['severity'],
            'weakness_score':         row['weakness_score'],
            'required_phase':         phase or 'All',
            'required_matchup':       ptype or 'N/A',
            'required_situation':     situation or 'N/A',
            'primary_metric':         prim_metric,
            'primary_threshold':      threshold,
            'required_pressure_min':  'Must beat IPL pressure avg',
            'required_roles':         str(roles),
            'priority_weight':        row['weakness_score'],
        }
        profiles.append(profile)

    if profiles:
        prof_df = pd.DataFrame(profiles)
        prof_df.to_csv(f'{OUT}/rr_required_player_profiles.csv', index=False)
        print(f"  Saved rr_required_player_profiles.csv ({len(prof_df)} profiles)")
        print("\n  REQUIRED PLAYER PROFILES:")
        for _, p in prof_df.head(8).iterrows():
            print(f"  [{p['weakness_rank']:2d}] {p['weakness_type']:8s} | "
                  f"{p['weakness_category']:30s} | {p['primary_metric']:20s} {p['primary_threshold']} | "
                  f"Roles: {p['required_roles'][:50]}")
    else:
        print("  No profiles generated")
        pd.DataFrame().to_csv(f'{OUT}/rr_required_player_profiles.csv', index=False)
else:
    print("  No weakness data — skipping profiles")
    pd.DataFrame().to_csv(f'{OUT}/rr_required_player_profiles.csv', index=False)

elapsed = time.time() - t0
print(f"\n{'=' * 70}")
print(f"PHASE 4 COMPLETE — {elapsed:.1f}s")
print(f"{'=' * 70}")
print(f"Output files:")
print(f"  → {OUT}/model_comparison.csv")
print(f"  → {OUT}/model_validation.csv")
print(f"  → {OUT}/rr_batting_analysis.csv")
print(f"  → {OUT}/rr_bowling_analysis.csv")
print(f"  → {OUT}/rr_weaknesses.csv")
print(f"  → {OUT}/rr_required_player_profiles.csv")
print(f"\nNEXT STEP: Run pipeline_p5_fit_rankings.py")
