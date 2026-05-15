import pandas as pd

# Load data
df = pd.read_csv("output/final_fiba_ncaa_copy.csv")
team_df = pd.read_csv("srs_10year/team_10year_summary.csv")
conf_df = pd.read_csv("srs_10year/conf_10year_summary.csv")
team_df['School'] = [x.replace("State", "St.") for x in team_df['School']]
print(df['made_d1'].value_counts())
# --------------------------------------------------
# TEAM LOOKUP
# --------------------------------------------------
team_lookup = dict(zip(team_df["School"], team_df["median_rank"]))

# map bestteam to rank
df["bestteam_rank"] = df["bestteam"].map(team_lookup).fillna(180)


# --------------------------------------------------
# TEAM MULTIPLIER (light influence)
# elite team ~1.03 / avg ~1.00 / bad ~0.97
# --------------------------------------------------
def team_mult(rank):
    pct = 1 - (rank / 360)
    return 0.97 + 0.09 * pct

df["team_mult"] = df["bestteam_rank"].apply(team_mult)


# --------------------------------------------------
# CONFERENCE MULTIPLIER
# based on long-term median strength
# stronger spread than team
# weak leagues penalized slightly
# --------------------------------------------------
conf_mult = {
    "Pac-12": 1.14,
    "Big 12": 1.13,
    "SEC": 1.13,
    "Big Ten": 1.12,
    "ACC": 1.12,

    "Big East": 1.05,
    "AAC": 1.03,
    "WCC": 1.02,
    "American": 1.01,
    "MWC": 1.01,

    "A-10": 1.01,
    "MAC": 1.01,
    "Ivy": 1.01,
    "MVC": 1.01,
    "CUSA": 1.0,

    "Summit": 1.0,
    "Big Sky": 1.0,

    "Horizon": 1.00,
    "Big West": 1.00,
    "CAA": 1.00,
    "Sun Belt": 1.00,

    "WAC": 0.99,
    "OVC": 0.99,
    "Patriot": 0.99,

    "A-Sun": 0.98,
    "AmEast": 0.98,
    "Southern": 0.98,
    "MAAC": 0.98,

    "Southland": 0.97,
    "Big South": 0.97,
    "MEAC": 0.97,
    "SWAC": 0.97,
    "NEC": 0.97,

    "Ind": 0.97
}

df["conf_mult"] = df["bestconf"].map(conf_mult).fillna(1.00)


# --------------------------------------------------
# FINAL LEAGUE-ADJUSTED BEST SEASON SCORE
# --------------------------------------------------
df["league_adj_best"] = (
    df["PER_best"] *
    df["conf_mult"] *
    df["team_mult"]
)


# --------------------------------------------------
# OPTIONAL CHECK
# --------------------------------------------------
df = df.sort_values("league_adj_best", ascending=False)
print(
    df.drop_duplicates(subset=["NAME"])[
        [
            "NAME",
            "bestteam",
            "bestconf",
            "PER_best",
            "bestteam_rank",
            "team_mult",
            "conf_mult",
            "league_adj_best",
        ]
    ].head(24)
)
df.to_csv("ML Pipeline/fiba_ncaa_weighted_score.csv",index=False)