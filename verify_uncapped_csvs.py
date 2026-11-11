import pandas as pd

files = [
    'results/uncapped_ipl2027_candidate_pool.csv',
    'results/uncapped_ipl2027_top10.csv',
    'results/uncapped_ipl2027_watchlist.csv'
]

for f in files:
    df = pd.read_csv(f)
    print(f"=== {f} ===")
    print(f"Rows: {len(df)}, Cols: {len(df.columns)}")
    nans = df.isna().sum()
    if nans.sum() > 0:
        print("NaNs found:")
        print(nans[nans > 0])
    else:
        print("ZERO NaNs detected across all columns! Perfectly clean.")

