from docling.document_converter import DocumentConverter
import re
import pandas as pd
from io import StringIO
import json
import re
from typing import Dict, Any, List, Tuple
from populate import add_match_data


def convert_to_md(url):
    "Converts a url to an md table"
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


def md_to_csv(md_table, out_file):
    rows = []
    for line in md_table.splitlines():
        line = line.strip()
        # skip separator lines (like ----)
        if set(line) <= {"|", "-", " "}:
            continue
        # remove leading/trailing | and collapse multiple spaces
        line = line.strip("|")
        line = re.sub(r"\s+", " ", line)
        rows.append(line)

    cleaned = "\n".join(rows)

    # Now parse into DataFrame
    df = pd.read_csv(StringIO(cleaned), sep="|")
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    df.to_csv(out_file, index=False)
    return df

TimeEntry = Tuple[str, str]                 # (time_str, is_own_goal)

# find team codes to make names smaller
with open('Data/teamCodes.json', 'r') as fp:
    team_codes = json.load(fp)
    
def extract_match_stats(md_text: str) -> Dict[str, Any]:
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
        "score": f"{home_score}-{away_score}",
        "home_team": home_team,
        "away_team": away_team,
        "home_scorers": home_scorers,
        "away_scorers": away_scorers,
        "stats": stats,
    }

import re
import json
from typing import Dict, Any, List, Tuple, Optional

def parse_match_file(md_text: str):
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
            #print(section)
            print("Extracting players:")
            #print(matches)
            for i, m in enumerate(matches):
                number = int(m.group(1))
                name = m.group(2).strip()
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

    """
    url = "https://www.fotmob.com/teams/8602/squad/wolverhampton-wanderers"
    team_name = url.rstrip("/").split("/")[-1]
    md_table = convert_to_md(url)
    team_name_corrected = team_name[0].upper() + team_name[1:]
    md_to_csv(md_table, f"Data/{team_name_corrected}.csv")
    """

    match_stats_url = "https://www.skysports.com/football/chelsea-vs-liverpool/stats/531193"
    stats_md = convert_to_md(match_stats_url)
    stats = extract_match_stats(stats_md)
    #print(stats)
    match_name = stats["match"]
    player_stats_url = match_stats_url.replace("/stats/", "/teams/")
    player_stats_md = convert_to_md(player_stats_url)
    player_stats = parse_match_file(player_stats_md)
   
    stats.update(player_stats)


    file = f"Data/Matches/{match_name}.json"
    with open(file, 'x') as fp:
        json.dump(stats, fp)

    add_match_data(file)