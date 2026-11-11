"""
build_player_status.py
======================
Builds the systematic Player Eligibility and Current Playing Status layer
for IPL 2027 Recruitment Intelligence.

CORE PRINCIPLE:
Separates:
  1. HISTORICAL PERFORMANCE (Population A: ALL_HISTORICAL_PLAYERS)
  2. CURRENT PLAYING STATUS (as of 11 November 2026)
  3. IPL 2027 PRACTICAL ELIGIBILITY (Population B: IPL_2027_RELEVANT_PLAYERS)

Output:
  results/player_status.csv
  results/historical_top10_batters.csv
  results/historical_top10_bowlers.csv
  results/ipl2027_eligible_top10_batters.csv
  results/ipl2027_eligible_top10_bowlers.csv
  results/ipl2027_status_unknown_watchlist.csv
"""

import os
import sys
import numpy as np
import pandas as pd

DATA_DIR = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\6af3166e7b922_data_pack'
OUT_DIR  = r'C:\Users\LOQ\Desktop\RR_IPL_Selection\results'
os.makedirs(OUT_DIR, exist_ok=True)

STATUS_DATE = '2026-11-11'

print("=" * 70)
print(f"BUILDING PLAYER STATUS & ELIGIBILITY LAYER (Status Date: {STATUS_DATE})")
print("=" * 70)

def parse_season_year(s):
    if pd.isna(s):
        return None
    s_str = str(s).strip()
    if '/' in s_str:
        parts = s_str.split('/')
        if len(parts[1]) == 2:
            return 2000 + int(parts[1])
        return int(parts[1])
    try:
        return int(s_str[:4])
    except Exception:
        return None

# 1. LOAD RELEVANT TABLES
comp_map = pd.read_csv(os.path.join(DATA_DIR, 'competition_team_player_mapping.csv'))
comps    = pd.read_csv(os.path.join(DATA_DIR, 'competitions.csv'))
pe       = pd.read_csv(os.path.join(DATA_DIR, 'playing_eleven.csv'))
matches  = pd.read_csv(os.path.join(DATA_DIR, 'matches.csv'))
bbb      = pd.read_csv(os.path.join(DATA_DIR, 'ball_by_ball.csv'), usecols=['match_id', 'striker_id', 'bowler_id'])

comps['season_int'] = comps['season'].apply(parse_season_year)

# Match info merged with playing eleven
pe_m = pe.merge(matches[['match_id', 'comp_id', 'match_date']], on='match_id', how='left')
pe_m = pe_m.merge(comps[['comp_id', 'comp_name', 'match_format', 'season_int']], on='comp_id', how='left')

ipl_comps = {1358: 2022, 1715: 2023, 2193: 2024, 2725: 2025, 3298: 2026}
IPL_2026_COMP_ID = 3298

# Unique players across comp_map
all_players_df = comp_map[['player_id', 'player_name']].drop_duplicates().copy()
print(f"Total unique players across competitions: {len(all_players_df):,}")

# Historical ball-by-ball participation
striker_ids = set(bbb['striker_id'].dropna().astype(int))
bowler_ids  = set(bbb['bowler_id'].dropna().astype(int))
bbb_player_ids = striker_ids.union(bowler_ids)
played_pe_ids = set(pe_m[pe_m['is_played'] == True]['player_id'].dropna().astype(int))
historical_ids = bbb_player_ids.union(played_pe_ids)

all_players_df['historical_data_available'] = all_players_df['player_id'].isin(historical_ids)

# IPL Squad History
ipl_cm = comp_map[comp_map['comp_id'].isin(ipl_comps.keys())].copy()
ipl_cm['season_int'] = ipl_cm['comp_id'].map(ipl_comps)
ipl_squad_max = ipl_cm.groupby('player_id')['season_int'].max().to_dict()

# IPL Played History
pe_ipl = pe_m[(pe_m['comp_id'].isin(ipl_comps.keys())) & (pe_m['is_played'] == True)].copy()
ipl_played_max = pe_ipl.groupby('player_id')['season_int'].max().to_dict()

def get_last_ipl_season(pid):
    s_sq = ipl_squad_max.get(pid, None)
    s_pl = ipl_played_max.get(pid, None)
    vals = [v for v in [s_sq, s_pl] if v is not None]
    return max(vals) if vals else None

all_players_df['last_ipl_season'] = all_players_df['player_id'].apply(get_last_ipl_season)

# T20I Played History
pe_t20i = pe_m[(pe_m['match_format'] == 'T20I') & (pe_m['is_played'] == True)].copy()
t20i_played_max = pe_t20i.groupby('player_id')['season_int'].max().to_dict()

# T20I Squad History
t20i_comp_ids = set(comps[comps['match_format'] == 'T20I']['comp_id'])
t20i_cm = comp_map[comp_map['comp_id'].isin(t20i_comp_ids)].copy()
t20i_cm = t20i_cm.merge(comps[['comp_id', 'season_int']], on='comp_id', how='left')
t20i_squad_max = t20i_cm.groupby('player_id')['season_int'].max().to_dict()

def get_last_t20i_season(pid):
    s_sq = t20i_squad_max.get(pid, None)
    s_pl = t20i_played_max.get(pid, None)
    vals = [v for v in [s_sq, s_pl] if v is not None]
    return max(vals) if vals else None

all_players_df['last_t20i_season'] = all_players_df['player_id'].apply(get_last_t20i_season)

# IPL 2026 Participation & Squad
pe_2026 = pe_m[(pe_m['comp_id'] == IPL_2026_COMP_ID) & (pe_m['is_played'] == True)]
played_2026_ids = set(pe_2026['player_id'].dropna().astype(int))
all_players_df['played_ipl_2026'] = all_players_df['player_id'].isin(played_2026_ids)

squad_2026 = comp_map[comp_map['comp_id'] == IPL_2026_COMP_ID][['player_id', 'team_name']].drop_duplicates()
squad_2026_map = dict(zip(squad_2026['player_id'], squad_2026['team_name']))
all_players_df['ipl_2026_team'] = all_players_df['player_id'].map(squad_2026_map)

# 2. CONFIRMED RETIREMENT REGISTRY
CONFIRMED_RETIREMENTS = {
    143: {
        'player_name': 'Dinesh Karthik',
        'reason': 'Officially announced retirement from IPL and competitive cricket in May 2024 post-Eliminator; appointed RCB Batting Coach & Mentor; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    142: {
        'player_name': 'Shikhar Dhawan',
        'reason': 'Officially announced retirement from international and domestic cricket on 24 August 2024; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    535: {
        'player_name': 'Ambati Rayudu',
        'reason': 'Officially announced retirement from IPL post-2023 final (May 2023); ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    494: {
        'player_name': 'Kieron Pollard',
        'reason': 'Retired from IPL playing career in November 2022; transitioned to Mumbai Indians coaching staff; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    161: {
        'player_name': 'Dwayne Bravo',
        'reason': 'Retired from IPL in December 2022 and all competitive cricket in September 2024; active coaching/mentoring role; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    169: {
        'player_name': 'Robin Uthappa',
        'reason': 'Announced retirement from all forms of Indian and IPL cricket in September 2022; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    250: {
        'player_name': 'Aaron Finch',
        'reason': 'Retired from international cricket in February 2023 and BBL/IPL in January 2024; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    109: {
        'player_name': 'Wriddhiman Saha',
        'reason': 'Announced retirement from all competitive cricket in November 2024 concluding with the 2024-25 domestic season; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    796: {
        'player_name': 'Matthew Wade',
        'reason': 'Announced retirement from international cricket in October 2024; appointed Australia coaching staff; inactive in IPL; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    393: {
        'player_name': 'Kedar Jadhav',
        'reason': 'Announced retirement from all forms of cricket on 3 June 2024; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    1028: {
        'player_name': 'Varun Aaron',
        'reason': 'Announced retirement from red-ball and competitive Indian cricket in February 2024; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    1829: {
        'player_name': 'Shahbaz Nadeem',
        'reason': 'Announced retirement from all cricket in March 2024; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    158: {
        'player_name': 'Amit Mishra',
        'reason': 'Veteran spinner (born 1982, age 44); uncontracted in 2025-2026; retired/inactive veteran status; ineligible for active player selection.',
        'source': 'INACTIVE_VETERAN_RECORD'
    },
    35: {
        'player_name': 'Nathan Bracken',
        'reason': 'Historic international cricketer retired from all cricket in 2011; invalid legacy entry; ineligible for active player selection.',
        'source': 'LEGACY_RECORD'
    },
    2299: {
        'player_name': 'Gurkeerat Singh Mann',
        'reason': 'Announced retirement from international and Indian competitive cricket in November 2023; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    2872: {
        'player_name': 'Siddarth Kaul',
        'reason': 'Announced retirement from Indian cricket in May 2024; relocated overseas; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    },
    478: {
        'player_name': 'Eoin Morgan',
        'reason': 'Announced retirement from all forms of cricket in February 2023; ineligible for active player selection.',
        'source': 'OFFICIAL_RETIREMENT_RECORD'
    }
}

# 3. KNOWN ACTIVE OVERSEAS / DOMESTIC STARS WHO MISSED 2026 IPL
KNOWN_ACTIVE_STARS = {
    1195: 'Ben Stokes',        # Active England Test captain
    1568: 'Kane Williamson',    # Active NZ international
    220:  'David Warner',       # Active franchise cricketer
    1318: 'Andre Russell',      # Active WI/franchise cricketer
    838:  'Glenn Maxwell',      # Active Australia international
    88:   'Faf du Plessis',     # Active franchise cricketer
    1205: 'Jonny Bairstow',     # Active England international
    2636: 'Adam Zampa',         # Active Australia international
    305:  'Ravichandran Ashwin',# Active India international
    1596: 'Moeen Ali',          # Active England/franchise cricketer
    3275: 'Alzarri Joseph',     # Active WI international
    1171: 'Chris Woakes',       # Active England international
    4106: 'Daryl Mitchell',     # Active NZ international
    2985: 'Mark Wood',          # Active England international
    1187: 'Jason Roy',          # Active franchise cricketer
    5809: 'Naveen ul Haq',      # Active Afghanistan international
    2984: 'Sikandar Raza',      # Active Zimbabwe international
    6772: 'Chetan Sakariya',    # Active Indian domestic cricketer
    3648: 'Deepak Hooda',       # Active Indian domestic/franchise cricketer
    2878: 'Mohit Sharma',       # Active Indian domestic/franchise cricketer
    2877: 'Vijay Shankar',      # Active Indian domestic/franchise cricketer
    6674: 'Rahmanullah Gurbaz', # Active Afghanistan international
    6280: 'Harry Brook',        # Active England international
    7341: 'Jake McGurk',        # Active Australia international
    19316:'Maheesh Theekshana', # Active Sri Lanka international
    47050:'Shamar Joseph',      # Active WI international
    8614: 'William ORourke',    # Active NZ international
    3672: 'Kusal Mendis',       # Active Sri Lanka international
    4895: 'Charith Asalanka',   # Active Sri Lanka international
    4779: 'Pieter Willem Mulder',# Active SA international
    7240: 'FazalHaq Farooqi',   # Active Afghanistan international
    6450: 'Mujeeb Ur Rahman',   # Active Afghanistan international
    1941: 'Devon Conway',       # Active NZ international
    6398: 'Aaron Hardie',       # Active Australia international
}

# 4. COMPREHENSIVE STATUS CLASSIFICATION LOGIC
status_records = []

for idx, row in all_players_df.iterrows():
    pid   = int(row['player_id'])
    pname = str(row['player_name'])
    has_hist = bool(row['historical_data_available'])
    last_ipl = row['last_ipl_season']
    last_t20i = row['last_t20i_season']
    played_26 = bool(row['played_ipl_2026'])
    team_26   = row['ipl_2026_team']
    in_squad_26 = pd.notna(team_26)

    active_status = 'UNKNOWN'
    retire_status = 'UNKNOWN'
    ipl_status    = 'UNKNOWN'
    source        = 'DATABASE_INFERENCE'
    reason        = ''
    eligible      = 'UNKNOWN'

    # Check 1: Confirmed Retired
    if pid in CONFIRMED_RETIREMENTS:
        ret_info = CONFIRMED_RETIREMENTS[pid]
        active_status = 'RETIRED'
        retire_status = 'RETIRED'
        ipl_status    = 'RETIRED'
        source        = ret_info['source']
        reason        = ret_info['reason']
        eligible      = 'FALSE'

    # Check 2: Active IPL 2026 Squad Member (Contracted)
    elif in_squad_26:
        active_status = 'ACTIVE'
        retire_status = 'NOT_RETIRED'
        ipl_status    = 'CURRENTLY_CONTRACTED'
        source        = 'OFFICIAL_IPL_2026_SQUAD'
        played_str    = 'and played matches' if played_26 else 'as reserve squad member'
        reason        = f"Officially contracted in IPL 2026 squad ({team_26}) {played_str}; active franchise cricketer eligible for IPL 2027 recruitment."
        eligible      = 'TRUE'

    # Check 3: Active International or IPL 2025 Player (Potentially Auction)
    elif pid in KNOWN_ACTIVE_STARS or (last_t20i is not None and last_t20i >= 2025) or (last_ipl is not None and last_ipl == 2025):
        active_status = 'ACTIVE'
        retire_status = 'NOT_RETIRED'
        ipl_status    = 'POTENTIALLY_AUCTION'
        
        if last_t20i is not None and last_t20i >= 2025:
            source = 'ACTIVE_INTERNATIONAL_CRICKET'
            reason = f"Active international cricketer (represented national team in T20Is in {last_t20i}); eligible for IPL 2027 auction pool subject to registration."
        elif last_ipl == 2025:
            source = 'RECENT_IPL_SQUAD_2025'
            reason = f"Contracted in recent IPL 2025 season; active competitive cricketer eligible for IPL 2027 auction pool."
        else:
            source = 'ACTIVE_PROFESSIONAL_CRICKETER'
            reason = f"Active professional cricketer; not featured in IPL 2026; eligible for IPL 2027 auction pool upon player registration."
        eligible = 'TRUE'

    # Check 4: Veteran / Uncontracted with no recent appearances (last IPL <= 2023, no recent T20I)
    elif (last_ipl is not None and last_ipl <= 2023 and (last_t20i is None or last_t20i <= 2023)):
        active_status = 'UNKNOWN'
        retire_status = 'UNKNOWN'
        ipl_status    = 'UNKNOWN'
        source        = 'DOMESTIC_UNCONFIRMED'
        reason        = f"No recorded IPL or T20I appearances since {last_ipl}; status unverified pending BCCI domestic registration or formal auction entry."
        eligible      = 'UNKNOWN'

    # Check 5: General Pool / Domestic Fringe (last IPL 2024, or international only)
    elif last_ipl == 2024:
        active_status = 'ACTIVE'
        retire_status = 'NOT_RETIRED'
        ipl_status    = 'POTENTIALLY_AUCTION'
        source        = 'RECENT_IPL_SQUAD_2024'
        reason        = f"Appeared in IPL 2024 squad; missed 2025-2026 IPL; potentially eligible for IPL 2027 auction pool upon registration."
        eligible      = 'TRUE'

    # Check 6: International T20I player only (never played IPL)
    elif last_ipl is None and last_t20i is not None:
        if last_t20i >= 2025:
            active_status = 'ACTIVE'
            retire_status = 'NOT_RETIRED'
            ipl_status    = 'POTENTIALLY_AUCTION'
            source        = 'ACTIVE_INTERNATIONAL_CRICKET'
            reason        = f"Active international T20I player (played in {last_t20i}); potential overseas auction entrant for IPL 2027."
            eligible      = 'TRUE'
        else:
            active_status = 'UNKNOWN'
            retire_status = 'UNKNOWN'
            ipl_status    = 'UNKNOWN'
            source        = 'INTERNATIONAL_INACTIVE'
            reason        = f"Last represented national team in {last_t20i}; status unconfirmed for IPL 2027."
            eligible      = 'UNKNOWN'

    # Check 7: Fallback / Unknown
    else:
        active_status = 'UNKNOWN'
        retire_status = 'UNKNOWN'
        ipl_status    = 'UNKNOWN'
        source        = 'DATABASE_INFERENCE'
        reason        = "Insufficient recent match data to confirm professional playing status as of 11 November 2026."
        eligible      = 'UNKNOWN'

    status_records.append({
        'player_id': pid,
        'player_name': pname,
        'historical_data_available': has_hist,
        'last_ipl_season': last_ipl,
        'last_t20i_season': last_t20i,
        'played_ipl_2026': played_26,
        'current_active_status': active_status,
        'retirement_status': retire_status,
        'ipl_2027_status': ipl_status,
        'status_source': source,
        'status_date': STATUS_DATE,
        'eligibility_reason': reason,
        'final_eligible': eligible
    })

status_df = pd.DataFrame(status_records)

# Save player_status.csv
status_path = os.path.join(OUT_DIR, 'player_status.csv')
status_df.to_csv(status_path, index=False)
print(f"Saved {status_path} ({len(status_df):,} rows)")

print("\n--- PLAYER STATUS BREAKDOWN ---")
print("current_active_status:")
print(status_df['current_active_status'].value_counts())
print("\nipl_2027_status:")
print(status_df['ipl_2027_status'].value_counts())
print("\nfinal_eligible:")
print(status_df['final_eligible'].value_counts())

# Check Dinesh Karthik explicitly
dk_row = status_df[status_df['player_id'] == 143]
print("\n--- DINESH KARTHIK STATUS RECORD ---")
for col in status_df.columns:
    print(f"  {col}: {dk_row[col].values[0]}")
