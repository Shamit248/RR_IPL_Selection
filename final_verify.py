import pandas as pd

status = pd.read_csv("results/player_status.csv")
dk_s = status[status["player_id"] == 143]
print("=== DINESH KARTHIK IN PLAYER_STATUS ===")
print("final_eligible:", dk_s["final_eligible"].values[0])
print("current_active_status:", dk_s["current_active_status"].values[0])
print("retirement_status:", dk_s["retirement_status"].values[0])
print("ipl_2027_status:", dk_s["ipl_2027_status"].values[0])
print("status_date:", dk_s["status_date"].values[0])
print("reason:", dk_s["eligibility_reason"].values[0])

rr_rankings = pd.read_csv("results/rr_ipl2027_rankings.csv")
dk_in_rr = rr_rankings[rr_rankings["player_id"] == 143]
print("\n=== DINESH KARTHIK IN RR_IPL2027_RANKINGS ===")
print("Found count:", len(dk_in_rr))

top10 = pd.read_csv("results/top10_summary.csv")
print("\n=== TOP 10 SUMMARY PLAYERS ===")
for idx, r in top10.iterrows():
    print(f"#{r['rank']}: {r['player_name']} ({r['determined_role']}) - Score: {r['RR_FIT_SCORE']:.2f} | Status: {r['ipl_2027_status']}")

hist_bat = pd.read_csv("results/historical_top10_batters.csv")
print("\n=== HISTORICAL TOP 10 BATTERS (POPULATION A) ===")
print(hist_bat[['rank', 'player_name', 'pressure_SR', 'bat_pressure_score', 'current_active_status', 'final_eligible']].to_string())

elig_bat = pd.read_csv("results/ipl2027_eligible_top10_batters.csv")
print("\n=== ELIGIBLE TOP 10 BATTERS (POPULATION B) ===")
print(elig_bat[['rank', 'player_name', 'pressure_SR', 'bat_pressure_score', 'ipl_2027_status']].to_string())
