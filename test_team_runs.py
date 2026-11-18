import pandas as pd

bbb = pd.read_csv('6af3166e7b922_data_pack/ball_by_ball.csv', low_memory=False)
mat = pd.read_csv('6af3166e7b922_data_pack/matches.csv', low_memory=False)

def get_team_runs(df):
    r = df['runs'].fillna(0)
    e2 = df['extras_2_runs'].fillna(0)
    et = df['extras_type']
    
    extra_run = et.isin(['wide', 'Overstep', 'legbyes', 'byes', 'other']).astype(int)
    # penalty
    penalty = (et == 'Penalty').astype(int) * 5
    
    return r + e2 + extra_run + penalty

bbb['calc_team_runs'] = get_team_runs(bbb)

sample_matches = mat['match_id'].head(10)
for mid in sample_matches:
    m_bbb = bbb[bbb['match_id'] == mid]
    m_info = mat[mat['match_id'] == mid].iloc[0]
    inn1 = m_bbb[m_bbb['innings'] == 1]['calc_team_runs'].sum()
    inn2 = m_bbb[m_bbb['innings'] == 2]['calc_team_runs'].sum()
    print(f"Match {mid}: Inn1={inn1}, Inn2={inn2} | Result={m_info['result']}")

