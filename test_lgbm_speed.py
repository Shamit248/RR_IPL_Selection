import pandas as pd
import numpy as np
import lightgbm as lgb
import time

print("Testing LightGBM model training on delivery context...")

# Load bbb
bbb = pd.read_csv('6af3166e7b922_data_pack/ball_by_ball.csv', low_memory=False)
bbb = bbb[bbb['innings'].isin([1, 2])].copy()

# Feature matrix
X = pd.DataFrame()
X['innings'] = bbb['innings'].astype('category')
X['overid'] = bbb['overid'].astype(float)
X['over_ball_num'] = bbb['over_ball_num'].astype(float)
X['batting_order'] = bbb['batting_order'].fillna(4).astype(float)
X['pace_or_spin'] = bbb['pace_or_spin'].fillna('Unknown').astype('category')
X['comp_id'] = bbb['comp_id'].astype('category') if 'comp_id' in bbb.columns else 1
# Wickets before
# If not yet computed, rough proxy overid
X['venue_id'] = 1  # placeholder

y_runs = bbb['runs'].fillna(0).astype(float)
y_wkt = (bbb['is_wicket'] == True).astype(int)

t0 = time.time()
reg = lgb.LGBMRegressor(n_estimators=100, max_depth=6, learning_rate=0.08, verbose=-1, random_state=42)
reg.fit(X, y_runs)
t_reg = time.time() - t0

t0 = time.time()
clf = lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.08, verbose=-1, random_state=42)
clf.fit(X, y_wkt)
t_clf = time.time() - t0

print(f"LGBMRegressor trained in {t_reg:.2f}s, mean predicted xRuns = {reg.predict(X).mean():.3f} vs actual = {y_runs.mean():.3f}")
print(f"LGBMClassifier trained in {t_clf:.2f}s, mean predicted xWkt = {clf.predict_proba(X)[:, 1].mean():.4f} vs actual = {y_wkt.mean():.4f}")

