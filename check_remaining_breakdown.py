import pandas as pd

# Load fit scores which has all 477 IPL players
fit = pd.read_csv("results/player_fit_scores.csv")
comp_map = pd.read_csv("6af3166e7b922_data_pack/competition_team_player_mapping.csv")
teams = pd.read_csv("6af3166e7b922_data_pack/teams.csv")

# Let us list every single player among the 477
all_477 = fit[['player_id', 'player_name', 'rr_squad_2026', 'first_ipl_season', 'seasons_in_ipl']].drop_duplicates().sort_values('player_name')

# Check overseas players
# All non-India international teams in teams.csv:
intl_non_india = set(teams[~teams['team_name'].str.contains('India|Chennai|Mumbai|Rajasthan|Punjab|Bengaluru|Bangalore|Delhi|Kolkata|Hyderabad|Gujarat|Lucknow', case=False, na=False)]['team_name'])
overseas_by_comp_map = set(comp_map[comp_map['team_name'].isin(intl_non_india)]['player_id'])

print(f"Overseas players identified via international matches in dataset: {len(overseas_by_comp_map)}")

# List the remaining players to check for any overseas players not in T20Is in dataset
rem = all_477[~all_477['player_id'].isin(overseas_by_comp_map)]
print(f"Remaining players: {len(rem)}")
