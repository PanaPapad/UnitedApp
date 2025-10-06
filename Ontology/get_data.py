import pandas as pd
import requests
from io import StringIO


def get_team_data():
    """
    Function to get a table with team information from wikipedia
    """
    url = "https://en.wikipedia.org/wiki/2025%E2%80%9326_Premier_League"

    # Add browser-like headers
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }

    # Get HTML content with requests
    response = requests.get(url, headers=headers)
    response.raise_for_status()


    # Now parse HTML with pandas
    tables = pd.read_html(StringIO(response.text))

    # Print all tables and their columns
    for i, table in enumerate(tables):
        print(f"Table {i}: {table.columns.tolist()}")

    # The stadiums/teams table is usually in index 1, but check the printout
    stadiums_table = tables[1]

    # Save to CSV
    stadiums_table.to_csv("data/premier_league_teams.csv", index=False, encoding="utf-8")

    print(stadiums_table)
    # manually added the code column

get_team_data()