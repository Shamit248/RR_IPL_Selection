"""
Test IPL eligibility and active filters
"""
import pandas as pd
import numpy as np

# Load files
DATA_DIR = "6af3166e7b922_data_pack"
mat = pd.read_csv(f"{DATA_DIR}/matches.csv", low_memory=False)
teams = pd.read_csv(f"{DATA_DIR}/teams.csv", low_memory=False)
comps = pd.read_csv(f"{DATA_DIR}/competitions.csv", low_memory=False)
cmap = pd.read_csv(f"{DATA_DIR}/competition_team_player_mapping.csv", low_memory=False)
bbb = pd.read_csv(f"{DATA_DIR}/ball_by_ball.csv", low_memory=False)

print("1. Identifying Pakistan-only players...")
# Identify Pakistan team_id(s)
pak_teams = teams[teams["team_name"].str.contains("Pakistan", case=False, na=False)]["team_id"].unique()
print("Pakistan team IDs:", pak_teams)

# Identify IPL competitions and IPL team IDs
ipl_comps = comps[comps["comp_name"].str.contains("IPL", case=False, na=False)]["comp_id"].unique()
print("IPL comp IDs:", ipl_comps)
ipl_teams = cmap[cmap["comp_id"].isin(ipl_comps)]["team_id"].unique()
print(f"IPL team count in cmap: {len(ipl_teams)}")

# Players mapped to Pakistan
pak_players = set(cmap[cmap["team_id"].isin(pak_teams)]["player_id"].unique())
print(f"Total players mapped to Pakistan: {len(pak_players)}")

# Players mapped to any IPL team
ipl_players = set(cmap[cmap["comp_id"].isin(ipl_comps)]["player_id"].unique())
print(f"Total players mapped to IPL teams: {len(ipl_players)}")

# Pakistan-only players = in pak_players but NOT in ipl_players
pak_only_players = pak_players - ipl_players
print(f"Pakistan-only players to exclude: {len(pak_only_players)}")

# Sample of Pakistan-only players
sample_pak = cmap[cmap["player_id"].isin(list(pak_only_players)[:5])][["player_id", "player_name"]].drop_duplicates()
print("Sample Pakistan-only players:", sample_pak.to_dict(orient="records"))

print("\n2. Identifying player latest match dates...")
# Merge bbb with matches to get match_date
m_dates = mat.set_index("match_id")["match_date"].to_dict()
bbb["match_date"] = bbb["match_id"].map(m_dates)

# Get latest match date for each striker and bowler
striker_dates = bbb.groupby("striker_id")["match_date"].max()
bowler_dates = bbb.groupby("bowler_id")["match_date"].max()

player_last_date = pd.concat([striker_dates, bowler_dates]).groupby(level=0).max().to_dict()

# Count active on or after 2025-01-01
active_players = {pid for pid, d in player_last_date.items() if str(d) >= "2025-01-01"}
inactive_players = {pid for pid, d in player_last_date.items() if str(d) < "2025-01-01"}
print(f"Total players with deliveries: {len(player_last_date)}")
print(f"Active players (last match >= 2025-01-01): {len(active_players)}")
print(f"Inactive players (last match < 2025-01-01): {len(inactive_players)}")

# Check sample size under pressure with temp_bbb_pi
pi_df = pd.read_feather("temp_bbb_pi.feather")
bbb["PI"] = pi_df["PI"]
bbb["is_batter_legal"] = (bbb["extras_type"] != "wide").astype(int)
bbb["is_bowler_legal"] = (~bbb["extras_type"].isin(["wide", "Overstep"])).astype(int)

hp_mask = bbb["PI"] >= 0.65
bat_hp_balls = bbb[hp_mask & (bbb["is_batter_legal"] == 1)].groupby("striker_id").size()
bowl_hp_balls = bbb[hp_mask & (bbb["is_bowler_legal"] == 1)].groupby("bowler_id").size()

print(f"\nBatters with >= 120 HP balls total: {(bat_hp_balls >= 120).sum()}")
print(f"Bowlers with >= 120 HP balls total: {(bowl_hp_balls >= 120).sum()}")

# Filtered pool:
qual_batters = [pid for pid, cnt in bat_hp_balls.items() if cnt >= 120 and pid in active_players and pid not in pak_only_players]
qual_bowlers = [pid for pid, cnt in bowl_hp_balls.items() if cnt >= 120 and pid in active_players and pid not in pak_only_players]

print(f"\nEligible Active Batters (>= 120 HP balls, active >= 2025-01-01, non-Pak): {len(qual_batters)}")
print(f"Eligible Active Bowlers (>= 120 HP balls, active >= 2025-01-01, non-Pak): {len(qual_bowlers)}")

name_map = cmap.drop_duplicates("player_id").set_index("player_id")["player_name"].to_dict()
print("\nSample Qualified Batters:")
for pid in qual_batters[:10]:
    print(f"  {pid}: {name_map.get(pid, 'Unknown')} | Last Date: {player_last_date.get(pid)} | HP Balls: {bat_hp_balls.get(pid)}")

print("\nSample Qualified Bowlers:")
for pid in qual_bowlers[:10]:
    print(f"  {pid}: {name_map.get(pid, 'Unknown')} | Last Date: {player_last_date.get(pid)} | HP Balls: {bowl_hp_balls.get(pid)}")

