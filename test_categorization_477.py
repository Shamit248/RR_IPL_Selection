import pandas as pd
from build_uncapped_recruitment_system import all_overseas_ids, all_senior_india_capped_ids
from audit_capped_by_name import senior_india_capped_names

fit = pd.read_csv('results/player_fit_scores.csv')

categories = []
for idx, r in fit.iterrows():
    pid = r['player_id']
    name = str(r['player_name']).strip().lower()
    
    if pid in all_overseas_ids:
        cat = 'OVERSEAS'
    elif pid in all_senior_india_capped_ids or name in senior_india_capped_names:
        cat = 'CAPPED_INDIAN'
    else:
        cat = 'UNCAPPED_INDIAN'
    categories.append(cat)

fit['player_category'] = categories
print("Player Category Distribution across all 477 players:")
print(fit['player_category'].value_counts())

