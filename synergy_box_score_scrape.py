from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd
import time
import numpy as np

import hashlib

def generate_player_id(name, country, year):
    key = f"{name.strip().lower()}_{country.strip().lower()}_{year}"
    return hashlib.md5(key.encode()).hexdigest()

countries_list = [
    "Australia",
    "Brazil",
    "Bulgaria",
    "Canada",
    "Croatia",
    "Czechia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Italy",
    "New Zealand",
    "Serbia",
    "Spain",
    "Sweden",
    "UK"
]

# Configuration
URL_LIST = [
    
    ("https://apps.synergysports.com/basketball/teams/5787f8e3576202139848e0d0/boxscore?seasonId=62022000ef4e6d1f884be241&competitionKey=54457dce300969b132fcfb41:ALL&perGame=true", "U18", "2022","Brazil"),
    ("https://apps.synergysports.com/basketball/teams/5787f8e3576202139848e0d0/boxscore?seasonId=60c6ff1ff172c7ea936560f4&competitionKey=54457dce300969b132fcfb41:ALL&perGame=true", "U18", "2021","Brazil"),
    ("https://apps.synergysports.com/basketball/teams/54457df8300969b132fd107c/boxscore?seasonId=62a653296b7b4c5617e75bd1&competitionKey=54457dce300969b132fcfb41:ALL&perGame=true", "U17", "2023","Brazil"),
    ("https://apps.synergysports.com/basketball/teams/5d067f8ff52909811e46bca7/boxscore?perGame=true&seasonId=62a653296b7b4c5617e75bd1&competitionKey=54457dce300969b132fcfb41:ALL", "U16", "2023","Brazil"),
    ("https://apps.synergysports.com/basketball/teams/5d067f8ff52909811e46bca7/boxscore?perGame=true&seasonId=60c6ff1ff172c7ea936560f4&competitionKey=54457dce300969b132fcfb41:ALL", "U16", "2021","Brazil"),
    ("https://apps.synergysports.com/basketball/teams/57b26d8057620213988e699c/boxscore?seasonId=684205c6d01c0c93c586dbf2&competitionKey=54457dce300969b132fcfb41:ALL&perGame=true","U19","2025","Brazil"),
    ("https://apps.synergysports.com/basketball/teams/57b26d8057620213988e699c/boxscore?seasonId=62a653296b7b4c5617e75bd1&competitionKey=54457dce300969b132fcfb41:ALL&perGame=true","U19","2023","Brazil")


]
currentcountry = 'brazil'

def scrape_synergy_data():
    driver = webdriver.Chrome()
    
    try:
        # Login once
        driver.get("https://apps.synergysports.com/basketball/games?leagueId=54457dce300969b132fcfb38&seasonId=68a4bdab3c211b288250118f&competitionKeys=54457dce300969b132fcfb38:CEE&teamAdjustedComparisonGroupId=648ac7b0a79824aa31db2b3b&playerImpactComparisonGroupId=648ac7b0a79824aa31db2b3d")

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "Username")))
        
        driver.find_element(By.NAME, "Username").send_keys("")
        driver.find_element(By.NAME, "Password").send_keys("")
        driver.find_element(By.CSS_SELECTOR, ".btn").click()
        time.sleep(2)
        
        all_players = []
        
        for url, fiba_class, fiba_year,fiba_country in URL_LIST:
            driver.get(url)
            time.sleep(3.5)  # Wait for page load
            
            # Extract data
            rows = driver.find_elements(By.CLASS_NAME, "cdk-row.ts-row.ng-star-inserted")
            
            for row in rows:
                try:
                    lines = row.text.split("\n")
                    if len(lines) >= 3:
                        name = ' '.join(lines[0].split()[1:])
                        player_data = {
                            "PLAYER_ID":generate_player_id(name,fiba_country,fiba_year),
                            "NAME": ' '.join(lines[0].split()[1:]),
                            "GP": lines[1],
                            "ROLE": lines[2] if len(lines) > 3 else None,
                            "COUNTRY": fiba_country,
                            "FIBA_CLASS": fiba_class,
                            "FIBA_YEAR": fiba_year,
                            "SCRAPE_TIMESTAMP": pd.Timestamp.now()
                        }
                        
                        # Add stats if available
                        if len(lines) >= 3:
                            stats = lines[-1].split()
                            stat_columns = ['POSS', 'PTS', 'PPP', 'AST', 'TO', 'FG%', '3FG_ATT', 
                                           '3FG%', 'EFG%', 'TOT_REB', 'FT_ATT', 'FT%', 'STL_BLK', 'AST_TO']
                            for col, val in zip(stat_columns, stats):
                                player_data[col] = val
                        
                        all_players.append(player_data)
                        
                except StaleElementReferenceException:
                    continue
            
        return pd.DataFrame(all_players)
    
    finally:
        driver.quit()

synergy_data = scrape_synergy_data()

col_order = ['NAME', 'GP', 'ROLE', 'COUNTRY', 'FIBA_CLASS', 'FIBA_YEAR', 'POSS', 'PTS', 'PPP', 'AST', 'TO', 'FG%', '3FG_ATT', '3FG%', 'EFG%', 'TOT_REB', 'FT_ATT', 'FT%', 'STL_BLK', 'AST_TO', 'PLAYER_ID', 'SCRAPE_TIMESTAMP']
synergy_data = synergy_data[[col for col in col_order if col in synergy_data.columns]]
print(synergy_data.head(3))
synergy_data.to_csv(f"synergy_scrapes/synergy_{currentcountry}.csv", index = False)