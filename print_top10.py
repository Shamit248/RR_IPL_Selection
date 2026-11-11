import pandas as pd
df = pd.read_csv("results/top10_summary.csv")
for idx, r in df.iterrows():
    print(f"#{r['rank']}: {r['player_name']} | Role: {r['determined_role']} | Score: {r['RR_FIT_SCORE']:.2f} | Pressure: {r['pressure_score']:.1f} | Weakness: {r['weakness_fit_score']:.1f} | Status: {r['ipl_2027_status']}")
    print(f"   Eligibility: {r['eligibility_reason']}")
