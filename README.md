# International Youth Basketball → NCAA Translation Pipeline

## Project Motivation

The central question behind this project is simple:

> **What can international youth basketball performance tell us about future NCAA success?**

Every summer, FIBA youth tournaments showcase hundreds of players from around the world. Some eventually become stars at the NCAA level. Others never reach Division I basketball at all. A smaller group becomes elite contributors despite modest early international production.

The challenge is that international scouting environments are noisy:

* Different countries play different styles
* Roles vary drastically
* Competition levels fluctuate
* Small sample sizes distort production
* Box score inflation exists in weaker pools
* Raw stats alone fail to capture long-term translation

This project attempts to bridge that gap by building a large merged dataset connecting:

1. **FIBA youth tournament performance**
2. **NCAA career outcomes**
3. **Team and conference strength adjustments**
4. **Weighted developmental scoring systems**

The final goal is not merely prediction.

Instead, the project aims to explore:

* developmental archetypes
* translation patterns
* role-based success paths
* international production signals
* NCAA environment effects
* and the relationship between youth efficiency and long-term collegiate impact

The resulting dataset contains **2,212 player rows** spanning multiple countries, age groups, and competition levels.

---

# Project Structure

The pipeline consists of four major components:

1. **Synergy/FIBA data scraping**
2. **NCAA Sports-Reference scraping**
3. **Weighted best-season evaluation**
4. **League and environment adjustment modeling**

Core scripts include:

* `synergy_box_score_scrape.py`
* `NCAA_Scraper.py`
* `weighted_score.py`
* final HTML/report outputs

---

# Dataset Overview

The final merged dataset contains the following columns:

```text
NAME
GP
ROLE
COUNTRY
FIBA_CLASS
FIBA_YEAR
POSS
PTS
PPP
AST
TO
FG%
3FG_ATT
3FG%
EFG%
TOT_REB
FT_ATT
FT%
STL_BLK
AST_TO
PTS/G_career
AST_career
TRB_career
STL_BLK_career
G_career
PER_career
best_season
bestteam
bestconf
PTS/G_best
AST_best
TRB_best
STL_BLK_best
PER_best
made_d1
bestteam_rank
team_mult
conf_mult
league_adj_best
```

Total rows: **2212**

Each row represents a FIBA youth tournament player merged with NCAA outcome information whenever available.

---

# Stage 1 — Collecting FIBA Youth Tournament Data

The first stage of the pipeline focuses on collecting international youth statistics from Synergy Sports.

The scraper automates:

* authentication
* tournament navigation
* box score extraction
* player parsing
* metadata tagging
* stat standardization

The process is handled through Selenium automation in:

`synergy_box_score_scrape.py`



The scraper iterates through tournament URLs containing:

* country
* age classification
* tournament season
* competition identifiers

Examples include:

* U16
* U17
* U18
* U19

Across countries such as:

* Brazil
* Canada
* Serbia
* France
* Spain
* Australia
* and others

For each player, the scraper extracts:

* possessions
* points
* points per possession
* assists
* turnovers
* shooting efficiency
* rebounding
* free throw rates
* steal/block combinations
* assist-to-turnover ratios

The scraper also generates a stable hashed player ID:

```python
def generate_player_id(name, country, year):
    key = f"{name.strip().lower()}_{country.strip().lower()}_{year}"
    return hashlib.md5(key.encode()).hexdigest()
```

This prevents duplicate identity collisions across tournaments and seasons.

The resulting international profile attempts to capture not just volume production, but efficiency, offensive role, and stylistic tendencies.

---

# Why Synergy Data Matters

Traditional FIBA box scores alone are often incomplete.

Synergy provides several advantages:

* possession-based normalization
* efficiency metrics
* role context
* offensive involvement
* scalable tournament scraping

This allows the dataset to move beyond simplistic “points per game” evaluation.

For example:

* two players may average identical scoring numbers
* but vastly different possession efficiency
* turnover profiles
* and offensive creation burden

That distinction becomes extremely important when evaluating future NCAA translation.

---

# Stage 2 — NCAA Career Outcome Collection

After collecting FIBA data, the next stage attempts to identify each player's NCAA career outcomes using Sports-Reference.

The pipeline:

1. Searches for matching player pages
2. Parses yearly NCAA statistics
3. Extracts career summaries
4. Computes simplified PER metrics
5. Identifies the player's best NCAA season

This process is handled in:

`NCAA_Scraper.py`



The scraper dynamically builds Sports-Reference URLs:

```python
search_name = name.lower().replace(" ", "-")
url = f"https://www.sports-reference.com/cbb/players/{search_name}-1.html"
```

The script then parses:

* season-by-season tables
* career rows
* conference identifiers
* team affiliations
* advanced stat components

---

# Simplified PER Calculation

One major challenge in NCAA translation analysis is creating a universal impact metric that works across all players.

The project uses a simplified PER-inspired formula:

```python
(
    PTS + AST + TRB + STL + BLK
    - TOV
    - missed FG
    - missed FT
) / G
```

This metric rewards:

* scoring
* creation
* rebounding
* defensive events

while penalizing:

* turnovers
* inefficiency

The implementation appears directly in the scraper:

```python
def calculate_per(row):
```



This is intentionally not identical to NBA PER.

Instead, it acts as a lightweight, interpretable all-in-one production metric suitable for large-scale NCAA comparisons.

---

# Parsing NCAA Career Histories

Sports-Reference pages are inconsistent.

Several edge cases required custom handling:

* missing position columns
* inconsistent “Career” rows
* team naming mismatches
* conference formatting issues
* duplicate school naming conventions

Examples include:

* `"State"` vs `"St."`
* `"Eastern Washington"` naming differences
* malformed table spacing

The scraper includes extensive parsing logic to standardize these cases before merging.

This stage ultimately produces:

* career averages
* best season metrics
* conference affiliation
* team strength context
* total games played
* NCAA participation indicators

---

# The Core Idea: Best Season Translation

One of the most important design choices in the project is this:

> The dataset evaluates players primarily through their BEST NCAA SEASON rather than full-career accumulation.

Why?

Because developmental trajectories differ dramatically.

Some players:

* peak early
* transfer repeatedly
* suffer injuries
* develop late
* or break out in specific systems

Using a player's best season captures:

* ceiling outcomes
* translated impact
* meaningful peak performance

rather than simply rewarding longevity.

This becomes the foundation for the weighted scoring pipeline.

---

# Stage 3 — Weighted Score Construction

The weighted score system is one of the most important components of the project.

The objective:

> Reward players who produced efficiently against stronger NCAA competition while maintaining meaningful sample sizes.

The weighted score combines:

1. Player efficiency (PER)
2. Number of games played
3. Team strength environment

The implementation appears in:

`NCAA_Scraper.py`



The formula:

```python
weighted_score =
    PER
    * sqrt(games)
    * team_strength
```

Where:

```python
pct = 1 - (teamrank / 360)
team_strength = 0.35 + 0.65 * (pct ** 2)
```

This creates several important behaviors:

### 1. Efficiency Matters Most

A highly productive player receives a strong base score.

### 2. Small Samples Are Penalized

Using:

```python
sqrt(games)
```

prevents tiny hot streaks from dominating the rankings.

### 3. Team Environment Matters

Players succeeding at stronger programs receive modest boosts.

However, the adjustment is intentionally restrained.

The project avoids over-crediting players simply because they attended elite schools.

---

# Understanding the SRS 10-Year Adjustment

The project uses long-term NCAA strength summaries stored in:

* `team_10year_summary.csv`
* `conf_10year_summary.csv`

These datasets represent approximate long-term program and conference strength using rolling SRS-style rankings.

The purpose is critical:

> NCAA production does not exist in a vacuum.

A 16 PER in the SEC is not necessarily equivalent to a 16 PER in a weak conference.

Similarly:

* elite teams create tougher internal competition
* stronger conferences suppress raw box score inflation
* weak leagues can artificially inflate counting stats

The project attempts to partially account for this reality.

---

# Team Multipliers

The first adjustment layer is team-level strength.

Implemented in:

`weighted_score.py`



The multiplier is intentionally conservative:

```python
def team_mult(rank):
    pct = 1 - (rank / 360)
    return 0.97 + 0.09 * pct
```

This creates only modest separation:

* elite teams ≈ 1.03
* average teams ≈ 1.00
* weak teams ≈ 0.97

The philosophy:

> Team quality should matter, but not overwhelm individual production.

---

# Conference Multipliers

Conference strength receives a stronger adjustment.

Examples:

```python
"Pac-12": 1.14
"Big 12": 1.13
"SEC": 1.13
"Big Ten": 1.12
"ACC": 1.12
```

while weaker leagues receive small penalties:

```python
"SWAC": 0.97
"NEC": 0.97
"Southland": 0.97
```

The final adjusted metric becomes:

```python
league_adj_best =
    PER_best
    * conf_mult
    * team_mult
```



This serves as the project's final “environment-adjusted best season” measurement.

---

# Why the Adjustments Matter

Without contextual adjustment:

* weak-conference stat inflation dominates
* volume scorers become overrated
* role players on elite teams become underrated
* cross-league comparisons break down

The adjustments are not meant to perfectly solve translation.

Instead, they attempt to create:

* more stable comparisons
* better developmental context
* less noisy ranking behavior

The model intentionally prioritizes interpretability over complexity.

---

# What the Dataset Can Explore

The merged dataset enables analysis across several dimensions:

## Development Pathways

Questions such as:

* Which FIBA archetypes succeed in NCAA basketball?
* Do efficient low-usage players translate better?
* Does shot creation matter more than scoring volume?
* Which age groups correlate most strongly with NCAA success?

---

## Country-Level Pipelines

The project can compare developmental systems across countries:

* Serbia
* Canada
* France
* Spain
* Australia
* Brazil
* and others

Potential questions include:

* Which countries produce the most NCAA-ready guards?
* Which systems emphasize efficiency?
* Which nations overperform relative to recruiting visibility?

---

## Role-Based Translation

Because the dataset includes role information and efficiency indicators, it can analyze:

* creators vs finishers
* shooters vs initiators
* low-usage efficiency players
* turnover-heavy primary handlers
* rebounding specialists

---

## NCAA Environment Effects

The SRS adjustments also allow exploration of:

* conference inflation
* mid-major translation
* power conference suppression effects
* elite team opportunity costs

---

# Important Limitations

This project is exploratory and intentionally imperfect.

Several limitations remain:

## Name Matching

International player naming conventions create ambiguity.

Some NCAA matches may be missed entirely.

---

## Missing Players

Not every international player reaches NCAA basketball.

Some:

* remain overseas
* play professionally
* enter JUCO systems
* or never appear in Sports-Reference

---

## Tournament Sample Sizes

FIBA youth tournaments are inherently small samples.

A player may only appear in:

* 5–7 games
* specific roles
* limited minutes
* unusual team contexts

---

## Simplified Metrics

The PER implementation is intentionally lightweight.

It is not equivalent to:

* NBA PER
* BPM
* RAPM
* Win Shares
* or advanced lineup models

---

## Manual Conference Weighting

Conference multipliers are heuristic-based.

They are designed for interpretability rather than strict optimization.

---

# Final Takeaways

The most important conclusion from this project is not:

> “International stats perfectly predict NCAA success.”

They do not.

Instead, the project demonstrates something more interesting:

> International youth basketball contains meaningful developmental signals — but those signals require contextual interpretation.

Raw scoring is insufficient.

Efficiency matters.

Role matters.

Environment matters.

Competition level matters.

And developmental pathways vary enormously.

The final distribution of NCAA outcomes is highly skewed:

* many players never become major contributors
* a moderate group becomes rotational college players
* a much smaller subset develops into elite NCAA performers

That asymmetry is central to the project.

The strongest insight from the analysis is that:

> translation patterns are probabilistic, structural, and archetype-dependent rather than deterministic.

In other words:

* certain player profiles consistently translate better
* certain environments amplify development
* and certain forms of international production appear more predictive than others

The project ultimately becomes less about “finding the next star” and more about:

> identifying meaningful developmental archetypes and understanding how international youth performance interacts with NCAA basketball environments.

That framing is both more realistic and more analytically valuable.
