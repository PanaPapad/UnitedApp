from docling.document_converter import DocumentConverter
import re
import pandas as pd
from io import StringIO
import json
import requests
from typing import Dict, Any, List, Tuple, Optional
from unidecode import unidecode
from populate import add_match_data

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

def convert_to_md(url):
    "Converts a url to an md table, by using DocumentConverter from docling"
    converter = DocumentConverter()
    result = converter.convert(url)
    mark = result.document.export_to_markdown()
    
    #print(mark)
    # only filter the tables (start with |)
    filtered = "\n".join(
        line for line in mark.splitlines() if line.startswith("|")
    )

    #print(filtered)
    return mark

# find team codes to make names smaller
with open('Data/teamCodes.json', 'r') as fp:
    team_codes = json.load(fp)
    
TimeEntry = Tuple[str, str]     # (time_str, is_own_goal)
def extract_match_stats(md_text: str, gameweek) -> Dict[str, Any]:
    """
    Returns a dict with:
      - score: "H-A"
      - home_team, away_team
      - home_scorers: List[ (player_name, [(time_str, is_own_goal), ...]) ]
      - away_scorers: same as home_scorers
      - stats: { stat_name: {"home": val, "away": val}, ... }

    Notes:
      - Lines like "- [Get Sky Sports](...)" are ignored (they don't match the player-name pattern).
      - Parentheses text is split by commas; each part is scanned for a time like "61'" or "90+3'".
      - An own-goal is detected if "og" or "own goal" appears in that part (case-insensitive).
    """

    # --- Team headers: e.g. "#### [Sunderland 3](\sunderland)" ---
    header_re = re.compile(r"^#### \[([^\]]*?)\s+(\d+)\]\(", re.M)
    headers = list(header_re.finditer(md_text))
    if len(headers) < 2:
        raise ValueError("Could not find two team headers with scores.")

    home_match, away_match = headers[0], headers[1]
    home_team, home_score = home_match.group(1).strip(), home_match.group(2)
    away_team, away_score = away_match.group(1).strip(), away_match.group(2)

    if home_team == "Brighton & Hove Albion":
        home_team = "Brighton and Hove Albion"
    # --- Sections ---
    match_stats_pos = re.search(r"^### Match Stats", md_text, re.M)
    home_section = md_text[home_match.end():away_match.start()]
    away_section = (
        md_text[away_match.end():match_stats_pos.start()]
        if match_stats_pos
        else md_text[away_match.end():]
    )
    stats_section = md_text[match_stats_pos.end():] if match_stats_pos else ""

    # --- Scorer line pattern ---
    # Only match lines where the name looks like "A Name" (starts with capital letter).
    # This avoids matching "- [Some Link](...)" or other link list items.
    scorer_line_re = re.compile(
        r"^- \s*([A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’\.\-\s]+?)\s*\(([^)]*)\)", re.M
    )

    time_re = re.compile(r"(\d+\+?\d*)")   # matches "61'", "90+3'" etc.

    def parse_scorers(section: str):# -> List[Scorer]:
        #scorers: List[Scorer] = []
        scorers = {}
        for m in scorer_line_re.finditer(section):
            name = m.group(1).strip()
            info = m.group(2).strip()   # inside the parentheses

            # split on commas (common separator for multiple goals), but tolerate missing commas
            parts = [p.strip() for p in re.split(r",\s*|\s{2,}", info) if p.strip()]

            # collect times (with own-goal flag) in the order of parts
            times: List[TimeEntry] = []
            for part in parts:
                # skip red cards
                if re.search(r"\b(red card|sent off|dismissed)\b", part, re.I):
                    continue
                # find the first time in this part
                t_match = time_re.search(part)
                if not t_match:
                    # if there's no explicit minute/time in the parentheses, skip this part
                    continue
                t = t_match.group(1)
                t.replace("'", "")
                is_og = bool(re.search(r"\b(og|own goal|own-goal)\b", part, re.I))
                is_pen = bool(re.search(r"\b(pen|penalty)\b", part, re.I))
                goal_info = None
                if is_og:
                    goal_info = "og"
                elif is_pen:
                    goal_info = "pen"
                if goal_info:
                    times.append([t, goal_info])
                else:
                    times.append([t, ""])
            # only add this scorer if we found at least one time entry (prevents link lines)
            if times:
                #scorers.append((name, times))
                scorers[name]= times

        return scorers

    home_scorers = parse_scorers(home_section)
    away_scorers = parse_scorers(away_section)

    # --- Stats extraction (same as before) ---
    stat_re = re.compile(
        r"^#####\s*(?P<name>.+?)\s*$"
        r"\s*^######\s*Home\s*$\s*"
        r"(?P<home>[^\r\n]+)\s*$\s*"
        r"^######\s*Away\s*$\s*"
        r"(?P<away>[^\r\n]+)\s*$",
        re.M,
    )

    stats = {
        m.group("name").strip(): {
            "home": m.group("home").strip(),
            "away": m.group("away").strip(),
        }
        for m in stat_re.finditer(stats_section)
    }

    home_team_code = team_codes[home_team]
    away_team_code = team_codes[away_team]

    return {
        "match": f"{home_team_code}_vs_{away_team_code}_PL25",
        "tournament": "PL_25",
        "gameweek": gameweek,
        "score": f"{home_score}-{away_score}",
        "home_team": home_team,
        "away_team": away_team,
        "home_scorers": home_scorers,
        "away_scorers": away_scorers,
        "stats": stats,
    }

def parse_match_file(md_text: str):
    """
    Function that parses the markdown text of a match teams page
    and returns a dictionary with home and away team players and their events.
    """
    def extract_teams_section(md_text):
        """Get everything under ## Teams until #### Key."""
        pattern = r"## Teams(.*?)#### Key"
        match = re.search(pattern, md_text, re.S)
        return match.group(1).strip() if match else ""

    def split_teams(teams_section: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Return: (home_team_name, home_team_block, away_team_name, away_team_block)
        or (None, None, None, None) if not enough team headers found.
        """
        # find all "#### <header>" occurrences (capture header text)
        matches = list(re.finditer(r"^####\s+([^\n\r]+)", teams_section, re.M))
        if len(matches) < 2:
            return None, None, None, None

        # take first two headers as home and away
        home_m = matches[0]
        away_m = matches[1]

        home_team_name = home_m.group(1).strip()
        away_team_name = away_m.group(1).strip()

        home_start = home_m.end()
        away_start = away_m.end()
        home_end = away_m.start()
        away_end = matches[2].start() if len(matches) > 2 else len(teams_section)

        home_block = teams_section[home_start:home_end].strip()
        away_block = teams_section[away_start:away_end].strip()

        # remove inline HTML image comments if present
        home_block = re.sub(r"<!--.*?-->\s*", "", home_block, flags=re.S).strip()
        away_block = re.sub(r"<!--.*?-->\s*", "", away_block, flags=re.S).strip()

        return home_team_name, home_block, away_team_name, away_block

    def parse_team_players(team_text: str):
        
        players = {}

        # Split into "starting XI" and "Substitutes" parts
        parts = re.split(r"#####\s*Substitutes", team_text)
        starters_text = parts[0].strip()
        subs_text = parts[1].strip() if len(parts) > 1 else ""

        def extract_players(section, is_starter=True):
            pattern = r"(\d+)\s*\n+(?:[A-Z]\s*\n+)?([A-Za-zÀ-ÿ'’\-]+(?: [A-Za-zÀ-ÿ'’\-]+)*)\s*(?:\(c\))?"
            matches = list(re.finditer(pattern, section))
            for i, m in enumerate(matches):
                number = int(m.group(1))
                name = m.group(2).strip()
                name = unidecode(name)
                is_captain = "(c)" in m.group(0)

                # Extract everything belonging to this player until the next one
                start = m.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
                player_block = section[start:end]

                data = {
                    "number": number,
                    "started": is_starter,
                    "isCaptain": is_captain,
                    "subbed_on": [],
                    "subbed_off": [],
                    "goals": [],
                    "assists": [],
                    "yellow_cards": [],
                    "red_cards": []
                }

                # Process each event line
                for line in player_block.splitlines():
                    line = line.strip()
                    if not line.startswith("-"):
                        continue
                    line = line[1:].strip()

                    minute_match = re.search(r"(\d+\+?\d*)'", line)

                    minute = minute_match.group(1) if minute_match else ""
                    if "Subbed on" in line:
                        data["subbed_on"].append(minute)
                    elif "Subbed off" in line:
                        data["subbed_off"].append(minute)
                    elif "Yellow card" in line:
                        data["yellow_cards"].append(minute)
                    elif "Red card" in line:
                        data["red_cards"].append(minute)
                    elif "Assist" in line:
                        data["assists"].append(minute)
                    elif "Goal scored" in line or "Penalty scored" in line or "Own goal" in line:
                        goal_type = ""
                        if re.search(r"\bpen", line, re.I):
                            goal_type = "pen"
                        elif re.search(r"\bown", line, re.I):
                            goal_type = "og"
                        data["goals"].append([minute, goal_type])

                players[name] = data

        extract_players(starters_text, is_starter=True)
        extract_players(subs_text, is_starter=False)
        return players

    # === Extract, split, and parse ===
    teams_section = extract_teams_section(md_text)
    home_name, home_block, away_name, away_block = split_teams(teams_section)

    if not home_block or not away_block:
        return {}

    home_players = parse_team_players(home_block)
    away_players = parse_team_players(away_block)

    return {
        "home_team_players": home_players,
        "away_team_players": away_players
    }

if __name__ == "__main__":

    PL_URLS ={ 
        1: [
            "https://www.skysports.com/football/liverpool-vs-bournemouth/stats/531129",
            "https://www.skysports.com/football/aston-villa-vs-newcastle-united/stats/531130",
            "https://www.skysports.com/football/brighton-and-hove-albion-vs-fulham/stats/531131",
            "https://www.skysports.com/football/sunderland-vs-west-ham-united/stats/531133",
            "https://www.skysports.com/football/tottenham-hotspur-vs-burnley/stats/531134",
            "https://www.skysports.com/football/wolverhampton-wanderers-vs-manchester-city/stats/531135",
            "https://www.skysports.com/football/chelsea-vs-crystal-palace/stats/531136",
            "https://www.skysports.com/football/nottingham-forest-vs-brentford/stats/531132",
            "https://www.skysports.com/football/manchester-united-vs-arsenal/stats/531137",
            "https://www.skysports.com/football/leeds-united-vs-everton/stats/531138"
        ],
        2: [
            "https://www.skysports.com/football/west-ham-united-vs-chelsea/stats/531148",
            "https://www.skysports.com/football/manchester-city-vs-tottenham-hotspur/stats/531146",
            "https://www.skysports.com/football/bournemouth-vs-wolverhampton-wanderers/stats/531140",
            "https://www.skysports.com/football/brentford-vs-aston-villa/stats/531141",
            "https://www.skysports.com/football/burnley-vs-sunderland/stats/531142",
            "https://www.skysports.com/football/arsenal-vs-leeds-united/stats/531139",
            "https://www.skysports.com/football/crystal-palace-vs-nottingham-forest/stats/531143",
            "https://www.skysports.com/football/everton-vs-brighton-and-hove-albion/stats/531144",
            "https://www.skysports.com/football/fulham-vs-manchester-united/stats/531145",
            "https://www.skysports.com/football/newcastle-united-vs-liverpool/stats/531147"

        ],
        3: [
            "https://www.skysports.com/football/sunderland-vs-brentford/stats/531156",
            "https://www.skysports.com/football/tottenham-hotspur-vs-bournemouth/stats/531157",
            "https://www.skysports.com/football/wolverhampton-wanderers-vs-everton/stats/531158",
            "https://www.skysports.com/football/leeds-united-vs-newcastle-united/stats/531152",
            "https://www.skysports.com/football/brighton-and-hove-albion-vs-manchester-city/stats/531150",
            "https://www.skysports.com/football/nottingham-forest-vs-west-ham-united/stats/531155",
            "https://www.skysports.com/football/liverpool-vs-arsenal/stats/531153",
            "https://www.skysports.com/football/aston-villa-vs-crystal-palace/stats/531149",
            "https://www.skysports.com/football/chelsea-vs-fulham/stats/531151",
            "https://www.skysports.com/football/manchester-united-vs-burnley/stats/531154",
        ],
        4: [
            "https://www.skysports.com/football/arsenal-vs-nottingham-forest/stats/531159",
            "https://www.skysports.com/football/bournemouth-vs-brighton-and-hove-albion/stats/531160",
            "https://www.skysports.com/football/crystal-palace-vs-sunderland/stats/531163",
            "https://www.skysports.com/football/everton-vs-aston-villa/stats/531164",
            "https://www.skysports.com/football/fulham-vs-leeds-united/stats/531165",
            "https://www.skysports.com/football/newcastle-united-vs-wolverhampton-wanderers/stats/531167",
            "https://www.skysports.com/football/west-ham-united-vs-tottenham-hotspur/stats/531168",
            "https://www.skysports.com/football/brentford-vs-chelsea/stats/531161",
            "https://www.skysports.com/football/burnley-vs-liverpool/stats/531162",
            "https://www.skysports.com/football/manchester-city-vs-manchester-united/stats/531166"

        ],
        5: [
            "https://www.skysports.com/football/liverpool-vs-everton/stats/531174",
            "https://www.skysports.com/football/brighton-and-hove-albion-vs-tottenham-hotspur/stats/531171",
            "https://www.skysports.com/football/burnley-vs-nottingham-forest/stats/531172",
            "https://www.skysports.com/football/west-ham-united-vs-crystal-palace/stats/531177",
            "https://www.skysports.com/football/wolverhampton-wanderers-vs-leeds-united/stats/531178",
            "https://www.skysports.com/football/manchester-united-vs-chelsea/stats/531175",
            "https://www.skysports.com/football/fulham-vs-brentford/stats/531173",
            "https://www.skysports.com/football/bournemouth-vs-newcastle-united/stats/531170",
            "https://www.skysports.com/football/sunderland-vs-aston-villa/stats/531176",   
            "https://www.skysports.com/football/arsenal-vs-manchester-city/stats/531169" 
        ],
        6: [
            "https://www.skysports.com/football/brentford-vs-manchester-united/stats/531180",
            "https://www.skysports.com/football/chelsea-vs-brighton-and-hove-albion/stats/531181",
            "https://www.skysports.com/football/crystal-palace-vs-liverpool/stats/531182",
            "https://www.skysports.com/football/leeds-united-vs-bournemouth/stats/531184",
            "https://www.skysports.com/football/manchester-city-vs-burnley/stats/531185",
            "https://www.skysports.com/football/nottingham-forest-vs-sunderland/stats/531187",
            "https://www.skysports.com/football/tottenham-hotspur-vs-wolverhampton-wanderers/stats/531188",
            "https://www.skysports.com/football/aston-villa-vs-fulham/stats/531179",
            "https://www.skysports.com/football/newcastle-united-vs-arsenal/stats/531186",
            "https://www.skysports.com/football/everton-vs-west-ham-united/stats/531183"
        ],
        7: [
            "https://www.skysports.com/football/bournemouth-vs-fulham/stats/531191",
            "https://www.skysports.com/football/leeds-united-vs-tottenham-hotspur/stats/531195",
            "https://www.skysports.com/football/arsenal-vs-west-ham-united/stats/531189",
            "https://www.skysports.com/football/manchester-united-vs-sunderland/stats/531196",
            "https://www.skysports.com/football/chelsea-vs-liverpool/stats/531193",
            "https://www.skysports.com/football/aston-villa-vs-burnley/stats/531190",
            "https://www.skysports.com/football/everton-vs-crystal-palace/stats/531194",
            "https://www.skysports.com/football/newcastle-united-vs-nottingham-forest/stats/531197",
            "https://www.skysports.com/football/wolverhampton-wanderers-vs-brighton-and-hove-albion/stats/531198",
            "https://www.skysports.com/football/brentford-vs-manchester-city/stats/531192"
        ],
        8: [
            "https://www.skysports.com/football/nottingham-forest-vs-chelsea/stats/531205",
            "https://www.skysports.com/football/brighton-and-hove-albion-vs-newcastle-united/stats/531199",
            "https://www.skysports.com/football/burnley-vs-leeds-united/stats/531200",
            "https://www.skysports.com/football/crystal-palace-vs-bournemouth/stats/531201",
            "https://www.skysports.com/football/sunderland-vs-wolverhampton-wanderers/stats/531206",
            "https://www.skysports.com/football/manchester-city-vs-everton/stats/531204",
            "https://www.skysports.com/football/fulham-vs-arsenal/stats/531202",
            "https://www.skysports.com/football/tottenham-hotspur-vs-aston-villa/stats/531207",
            "https://www.skysports.com/football/liverpool-vs-manchester-united/stats/531203",
            "https://www.skysports.com/football/west-ham-united-vs-brentford/stats/531208"
        ],
        9: [
            "https://www.skysports.com/football/arsenal-vs-crystal-palace/stats/531209",
            "https://www.skysports.com/football/aston-villa-vs-manchester-city/stats/531210",
            "https://www.skysports.com/football/bournemouth-vs-nottingham-forest/stats/531211",
            "https://www.skysports.com/football/brentford-vs-liverpool/stats/531212",
            "https://www.skysports.com/football/chelsea-vs-sunderland/stats/531213",
            "https://www.skysports.com/football/everton-vs-tottenham-hotspur/stats/531214",
            "https://www.skysports.com/football/leeds-united-vs-west-ham-united/stats/531215",
            "https://www.skysports.com/football/manchester-united-vs-brighton-and-hove-albion/stats/531216",
            "https://www.skysports.com/football/newcastle-united-vs-fulham/stats/531217",
            "https://www.skysports.com/football/wolverhampton-wanderers-vs-burnley/stats/531218"

        ],
        10: [
            "https://www.skysports.com/football/brighton-and-hove-albion-vs-leeds-united/stats/531219",
            "https://www.skysports.com/football/burnley-vs-arsenal/stats/531220",
            "https://www.skysports.com/football/crystal-palace-vs-brentford/stats/531221",
            "https://www.skysports.com/football/fulham-vs-wolverhampton-wanderers/stats/531222",
            "https://www.skysports.com/football/nottingham-forest-vs-manchester-united/stats/531225",
            "https://www.skysports.com/football/tottenham-hotspur-vs-chelsea/stats/531227",
            "https://www.skysports.com/football/liverpool-vs-aston-villa/stats/531223",
            "https://www.skysports.com/football/west-ham-united-vs-newcastle-united/stats/531228",
            "https://www.skysports.com/football/manchester-city-vs-bournemouth/stats/531224",
            "https://www.skysports.com/football/sunderland-vs-everton/stats/531226"
        ],
    }

    # for every gameweek and every match in that gameweek parse match stats and player stats and combine them
    # then save them to a json file
    for gameweek, urls in PL_URLS.items():
        if gameweek !=10:
            continue

        for match_stats_url in urls:
            # convert match stats page to md
            stats_md = convert_to_md(match_stats_url)
            # extract match stats
            stats = extract_match_stats(stats_md, gameweek)
            match_name = stats["match"]
            # get player stats url by replacing /stats/ with /teams/
            player_stats_url = match_stats_url.replace("/stats/", "/teams/")
            # convert player stats page to md
            player_stats_md = convert_to_md(player_stats_url)
            # extract player stats
            player_stats = parse_match_file(player_stats_md)
            # combine match stats and player stats (dictionaries)
            stats.update(player_stats)

            # save combined stats to json file
            file = f"Data/Matches/{gameweek}/Jsons/{match_name}.json"
            with open(file, 'x') as fp:
                json.dump(stats, fp)

            # create RDF data from the json file 
            add_match_data(file)