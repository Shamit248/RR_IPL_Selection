import pandas as pd

df = pd.read_csv('results/rr_ipl2027_final_top10.csv')
print("| Rank | Player | Category | Role | RR Problem Solved | Pressure Score | Reliability | Availability Probability | Final Fit Score | Recommendation |")
print("| :---: | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |")
for idx, r in df.iterrows():
    print(f"| {r['rank']} | {r['player_name']} | {r['player_category']} | {r['primary_role']} | {r['primary_problem_solved']} | {r['pressure_score']:.2f} | {r['reliability_score']:.2f} | {r['availability_probability']:.2f} | {r['final_rr_2027_fit_score']:.2f} | {r['recommendation']} |")

