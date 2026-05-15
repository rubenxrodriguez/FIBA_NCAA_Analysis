import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time,random
import numpy as np
import requests
from bs4 import BeautifulSoup
def calculate_per(row):
    """Calculate simplified PER"""
    return (
        (
            row['PTS'] + row['AST'] + row['TRB'] + row['STL'] + row['BLK']
            - row['TOV']
            - (row['FGA'] - row['FG'])
            - (row['FTA'] - row['FT'])
        ) / row['G']
    )


def safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default


def safe_int(x, default=0):
    try:
        return int(float(x))
    except:
        return default

def get_pts(row_str):
    parts = row_str.split()
    
    # If last value is numeric → no awards
    if parts[-1].replace('.', '', 1).isdigit():
        return float(parts[-1])
    
    # Otherwise last is awards → PTS is second-to-last
    return float(parts[-2])


def extract_season_team_conf_and_stats(row_str, team_names, conf_names, headers):
    """
    Parse one season row into:
    season, team, conf, stats_list
    """

    parts = row_str.split()
    season = parts[0]
    remaining_str = " ".join(parts[1:])

    # -------- TEAM --------
    sorted_teams = sorted(team_names, key=lambda x: -len(x.split()))

    team = None
    for t in sorted_teams:
        if remaining_str.startswith(t + " "):
            team = t
            remaining_str = remaining_str[len(t):].strip()
            break

    if team is None:
        return None

    # -------- CONF --------
    sorted_confs = sorted(conf_names, key=lambda x: -len(x.split()))

    conf = None
    for c in sorted_confs:
        if remaining_str.startswith(c + " "):
            conf = c
            remaining_str = remaining_str[len(c):].strip()
            break

    if conf is None:
        return None

    # -------- STATS --------
    stats = remaining_str.split()

    # Missing position column
    if len(stats) > 1 and stats[1].replace(".", "", 1).isdigit():
        stats.insert(1, "na")

    # Ensure awards column exists
    expected_len = len(headers[3:])
    if len(stats) < expected_len:
        stats += [""] * (expected_len - len(stats))

    return season, team, conf, stats
def get_team_rank(team_name):
    vals = team_df.loc[
        team_df["School"] == team_name,
        "median_rank"
    ].values
    
    if len(vals) == 0:
        return 180   # neutral fallback
    
    return float(vals[0])

def parse_row(row_str, team_names, conf_names, headers):
    """
    Fully parse one season row into structured object.
    """

    parsed = extract_season_team_conf_and_stats(
        row_str, team_names, conf_names, headers
    )

    if parsed is None:
        return None

    season, team, conf, stats = parsed

    try:
        stats_dict = dict(zip(headers[3:], stats))

        games = safe_int(stats_dict["G"])
        if games == 0:
            return None

        per = calculate_per({
            'PTS': safe_float(stats_dict['PTS']) * games,
            'AST': safe_float(stats_dict['AST']) * games,
            'TRB': safe_float(stats_dict['TRB']) * games,
            'STL': safe_float(stats_dict['STL']) * games,
            'BLK': safe_float(stats_dict['BLK']) * games,
            'TOV': safe_float(stats_dict['TOV']) * games,
            'FG': safe_float(stats_dict['FG']) * games,
            'FGA': safe_float(stats_dict['FGA']) * games,
            'FT': safe_float(stats_dict['FT']) * games,
            'FTA': safe_float(stats_dict['FTA']) * games,
            'G': games
        })

        return {
            "season": season,
            "team": team,
            "conf": conf,
            "games": games,
            "pts": safe_float(stats_dict["PTS"]),
            "ast": safe_float(stats_dict["AST"]),
            "trb": safe_float(stats_dict["TRB"]),
            "stl_blk": safe_float(stats_dict["STL"]) + safe_float(stats_dict["BLK"]),
            "per": per,
            "stats": stats_dict
        }

    except:
        return None


# =====================================================
# MAIN LOOP
# =====================================================



HEADERS = {"User-Agent": "Mozilla/5.0"}

fiba_df = pd.read_csv("synergy_scrapes/merged_synergy_data.csv")

team_df = pd.read_csv("srs_10year/team_10year_summary.csv")
conf_df = pd.read_csv("srs_10year/conf_10year_summary.csv")

team_names = team_df["School"].unique()
team_names = [x.replace("State", "St.") for x in team_names]
team_lookup = dict(zip(team_df["School"], team_df["median_rank"]))
conf_names = conf_df["Conf"].unique()

ncaa_stats = []
players_with_pages = []

print(f"players to scrape: {len(fiba_df['NAME'].unique())}")

for name in fiba_df["NAME"].unique():
#for name in debug_players:

    try:
        print(f"Processing {name}...")

        search_name = name.lower().replace(" ", "-")
        url = f"https://www.sports-reference.com/cbb/players/{search_name}-1.html"

        time.sleep(random.uniform(1, 3))
        response = requests.get(url, headers=HEADERS)
        time.sleep(random.uniform(2,4))
        if response.status_code != 200:
            print(f"No page found for {name}")
            continue

        players_with_pages.append(name)

        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.find("table", {"id": "players_per_game"})

        if table is None:
            print(f"No stats table for {name}")
            ncaa_stats.append({
                "NAME": name,
                "made_d1": 1,
                "PER_career":0.01,
            })
            continue

        rows = table.find_all("tr")
        headers = [th.text.strip() for th in rows[0].find_all("th")]

        row_strings = []
        career_data = {}

        # ==========================================
        # COLLECT ROWS + CAREER
        # ==========================================
        for row in rows[1:]:

            cols = [x.text.strip() for x in row.find_all(["td", "th"])]

            if not cols:
                continue

            # SportsRef weird Career row spacing
            if cols[0] == "Career" and len(cols) > 1:
                cols.pop(1)

            row_str = " ".join(cols)
            row_strings.append(row_str)

            # Career row
            if cols[0] == "Career":

                stats = cols
                headers_trimmed = [headers[0]] + headers[5:]

                career_stats = dict(zip(headers_trimmed, stats))

                g = safe_int(career_stats["G"])

                if g > 0:

                    career_data = {
                        "NAME": name,
                        "PTS/G_career": safe_float(career_stats["PTS"]),
                        "AST_career": safe_float(career_stats["AST"]),
                        "TRB_career": safe_float(career_stats["TRB"]),
                        "STL_BLK_career":
                            safe_float(career_stats["STL"]) +
                            safe_float(career_stats["BLK"]),
                        "G_career": g
                    }

                    career_data["PER_career"] = calculate_per({
                        'PTS': safe_float(career_stats['PTS']) * g,
                        'AST': safe_float(career_stats['AST']) * g,
                        'TRB': safe_float(career_stats['TRB']) * g,
                        'STL': safe_float(career_stats['STL']) * g,
                        'BLK': safe_float(career_stats['BLK']) * g,
                        'TOV': safe_float(career_stats['TOV']) * g,
                        'FG': safe_float(career_stats['FG']) * g,
                        'FGA': safe_float(career_stats['FGA']) * g,
                        'FT': safe_float(career_stats['FT']) * g,
                        'FTA': safe_float(career_stats['FTA']) * g,
                        'G': g
                    })

        # ==========================================
        # PARSE ALL VALID SEASON ROWS
        # ==========================================
        parsed_rows = []

        for row in row_strings:
            parsed = parse_row(row, team_names, conf_names, headers)

            if parsed is not None:
                parsed_rows.append(parsed)
            if row.split()[0] == 'Career':
                break
        if not parsed_rows:
            print(f"No valid season rows for {name}")
            continue

        # ==========================================
        # BEST SEASON
        # ==========================================

        for row in parsed_rows:
    
            
            teamrank = team_lookup.get(row['team'],180) # default to neutral if team not found
            
            pct = 1 - (teamrank/360)
            team_strength = 0.35+0.65*(pct**2)
            weighted_score = row['per']*(row['games']**0.5)*team_strength
            row['weighted_score'] = weighted_score
            print(f"{row['season']} - {row['team']} - PER: {row['per']:.2f}, Games: {row['games']}, Team Strength: {team_strength:.2f}, Weighted Score: {weighted_score:.2f}")

        best_row = max(parsed_rows, key=lambda x: x["weighted_score"])

        career_data.update({
            "NAME": name,
            "best_season": best_row["season"],
            "bestteam": best_row["team"],
            "bestconf": best_row["conf"],
            "PTS/G_best": best_row["pts"],
            "AST_best": best_row["ast"],
            "TRB_best": best_row["trb"],
            "STL_BLK_best": best_row["stl_blk"],
            "PER_best": best_row["per"]
        })

        # round numerics
        for k, v in career_data.items():
            if isinstance(v, float):
                career_data[k] = round(v, 2)

        ncaa_stats.append(career_data)

        print(f"Scraped {name} successfully")

    except Exception as e:
        print(f"Error processing {name}: {e}")
        continue

print(ncaa_stats)
# =====================================================
# MERGE BACK
# =====================================================


result_df = pd.merge(
    fiba_df,
    pd.DataFrame(ncaa_stats),
    on="NAME",
    how="left"
)

pd.DataFrame(players_with_pages, columns=["NAME"]).to_csv(
    "has_page.csv", index=False
)

#result_df["made_d1"] = result_df["PER_career"].notna().astype(int)
result_df.to_csv("fiba_ncaa_data.csv", index=False)
print("Done.")

