from rdflib import Graph, Namespace, RDF, URIRef, Literal
from rdflib.namespace import RDFS, DC, XSD
import requests
import pandas as pd
import json

def post_toGraphDB(data):
    """
    Function that posts a ttl file to GraphDB
    """
    url = "http://localhost:7200/repositories/UnitedApp/statements"

    headers = {'Content-Type': 'text/turtle',}

    response = requests.post(url, data=data.encode('utf=8'), headers=headers)
    if response.status_code == 204:
        print('Data successfully added to GraphDB.')
    else:
        print(f'Error adding data to GraphDB: {response.status_code}')
        print(response.text)

def add_players(team_name):
    """
    Function that reads from a csv data about players and creates a graph
    """
    g = Graph()
    #g.parse("unitedOntology.owl", format="xml")
    UO = Namespace("http://semanticweb.org/unitedOntology#")
    g.bind("uo", UO)
    df = pd.read_csv(f"Data/{team_name}.csv")
    team_URI = URIRef(UO + team_name.replace(" ", "_"))
    
    for idx, row in df.iterrows():
        print(row.keys())
        player_name = row["Player"]
        position = row["Position"]
        player_URI = URIRef(UO + player_name.replace(" ", "_"))
        g.add((player_URI, RDFS.label, Literal(player_name,  datatype=XSD.string)))
        if position == "Coach":
            g.add((player_URI, RDF.type, UO.Coach))
            g.add((player_URI, UO.coachesTeam, team_URI))
        else:
            g.add((player_URI, RDF.type, UO.Player))
            g.add((player_URI, UO.playsFor, team_URI))
            for p in position.split():
                print(p)
                positionURI = URIRef(UO + p)
                g.add((player_URI, UO.hasPosition, positionURI))
        
        g.add((player_URI, UO.hasNationality, Literal(row["Country"], datatype=XSD.string)))

    rdf_data = g.serialize(format='turtle')
    post_toGraphDB(rdf_data)

    for s,p,o in g.triples((None, None, None)):
        print(s,p,o)

def find_player(player_name, team_name=None):
    """
    Function that finds a player in graphDB and returns its URI
    """
    name_parts = player_name.split()
    values_block = " ".join(f'"{part}"' for part in name_parts)

    url = "http://localhost:7200/repositories/UnitedApp"
    # Split and lowercase
    parts = player_name.lower().split()

    # Build regex filters dynamically
    regex_filters = " || ".join([f'REGEX(LCASE(STR(?label)), "\\\\b{p}\\\\b", "i")' for p in parts])

    query = f"""
    PREFIX : <http://semanticweb.org/unitedOntology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?player WHERE {{
    ?player a :Player ;
            :playsFor :{team_name} ;
            rdfs:label ?label .
    FILTER({regex_filters})
    }}
    """
    
    headers = {
        'Accept': 'application/sparql-results+json',
        'Content-Type': 'application/sparql-query',
    }

    response = requests.post(url, data=query.encode('utf-8'), headers=headers)
    if response.status_code == 200:
        results = response.json()
        if results["results"]["bindings"]:
            player_uri = results["results"]["bindings"][0]["player"]["value"]
            #print(f"Player found: {player_uri}")
            return player_uri
        else:
            #print("Player not found.")
            return None
    else:
        print(f"Error querying GraphDB: {response.status_code}")
        print(response.text)
        return None

def add_team_data():
    """
    Function that reads data from a csv file about teams and creates a graph
    """
    # Load ontology
    g = Graph()
    g.parse("unitedOntology.owl", format="xml")

    # Namespaces
    UO = Namespace("http://semanticweb.org/unitedOntology#")
    g.bind("uo", UO)

    df = pd.read_csv("Data/premier_league_teams.csv")

    # Show the first few rows
    print(df.head())

    # Access columns
    print(df["Team"])          # example: list all team names
    print(df["Stadium"])       # example: list all stadiums

    # Iterate row by row
    for idx, row in df.iterrows():
        print(f"{row['Team']} play at {row['Stadium']} ({row['Capacity']})")
        team = row['Team']
        teamURI = URIRef(UO + team.replace(" ", "_"))
        g.add((teamURI, RDF.type, UO.Team))
        g.add((teamURI, RDFS.label, Literal(team,  datatype=XSD.string)))

        stadium = row['Stadium']
        stadiumURI = URIRef(UO + stadium.replace(" ", "_"))
        g.add((stadiumURI, RDF.type, UO.Stadium))
        g.add((stadiumURI, RDFS.label, Literal(stadium,  datatype=XSD.string)))

        # team homeStadium stadium
        g.add((teamURI, UO.homeStadium, stadiumURI))

        capacity = int(row["Capacity"])
        g.add((stadiumURI, UO.hasCapacity, Literal(capacity,  datatype=XSD.integer)))

        team_code = row["Code"]
        g.add((teamURI, UO.teamHasCode, Literal(team_code,  datatype=XSD.string)))

    rdf_data = g.serialize(format='turtle')
    
    post_toGraphDB(rdf_data)

# find team codes to make names smaller
with open('Data/teamCodes.json', 'r') as fp:
    team_codes = json.load(fp)
    fp.close()

def add_match_data(match_file):
    """
    Function that reads a json file with match data, creates a graph and uploads them to graphDB
    """

    def parse_minute(minute_str):
        """Convert minute strings like '45+3' or '90+2' to integer values."""
        if not minute_str:
            return 0
        try:
            if '+' in minute_str:
                base, extra = minute_str.split('+')
                return int(base) + int(extra)
            return int(minute_str)
        except ValueError:
            return 0


    def calculate_minutes_played(started, subbed_on, subbed_off):
        """
        Calculate minutes played by a player based on whether they started, 
        were subbed on or off, handling '45+3', '90+2', etc.
        """
        if started:
            if subbed_off:
                return parse_minute(subbed_off[0])
            else:
                return 90
        else:
            if subbed_on and subbed_off:
                return parse_minute(subbed_off[0]) - parse_minute(subbed_on[0])
            elif subbed_on and not subbed_off:
                mins = 90 - parse_minute(subbed_on[0])
                if mins < 0:
                    return 1 # if subbed on at 90+ return 1 minute played
                else:
                    return mins
            else:
                return 0

    def find_assist(goal_time, all_players):
        """
        Find the player who made the assist for a goal at a specific time
        """
        for playerURI, pdata in all_players.items():
            assists = pdata["assists"]
            if goal_time in assists:
                return playerURI
        return None

    def find_goal_order(goals_sorted, goal_time):
        order = 1
        for goal in goals_sorted:
            if goal == goal_time:
                return order
            order += 1

    # open file and read data
    with open(match_file, 'r') as fp:
        match_data = json.load(fp) 
        fp.close()

    # read data 
    # find team codes for shorter names
    home_team_code = team_codes[match_data["home_team"]]
    away_team_code = team_codes[match_data["away_team"]]
    match_name = match_data["match"].replace(" ", "_")
    home_team = match_data["home_team"].replace(" ","_")
    away_team = match_data["away_team"].replace(" ", "_")
    score = match_data["score"]
    home_goals, away_goals = map(int, score.split("-"))
    home_scorers = match_data["home_scorers"]
    away_scorers = match_data["away_scorers"]
    stats = match_data["stats"]
    possesion_home = stats["Possession %"]["home"]
    possesion_away = stats["Possession %"]["away"]
    total_shots_home = stats["Total Shots"]["home"]
    total_shots_away = stats["Total Shots"]["away"]
    on_target_home = stats["On Target"]["home"]
    on_target_away = stats["On Target"]["away"]
    corners_home = stats["Corners"]["home"]
    corners_away = stats["Corners"]["away"]
    offsides_home = stats["Offsides"]["home"]
    offsides_away = stats["Offsides"]["away"]
    aerial_duels_home = stats["Aerial Duels %"]["home"]
    aerial_duels_away = stats["Aerial Duels %"]["away"]
    saves_home = stats["Saves"]["home"]
    saves_away = stats["Saves"]["away"]
    fouls_commited_home = stats["Fouls Committed"]["home"]
    fouls_commited_away = stats["Fouls Committed"]["away"]
    fouls_won_home = stats["Fouls Won"]["home"]
    fouls_won_away = stats["Fouls Won"]["away"]
    yellow_cards_home = stats["Yellow Cards"]["home"]
    yellow_cards_away = stats["Yellow Cards"]["away"]


    g = Graph()
    #g.parse("unitedOntology.owl", format="xml")
    UO = Namespace("http://semanticweb.org/unitedOntology#")
    g.bind("uo", UO)

    # create match, home, away team URI
    matchURI = URIRef(UO+f"{match_name}")
    home_teamURI = URIRef(UO+home_team)
    away_teamURI = URIRef(UO+away_team)
    g.add((matchURI, RDF.type, UO.Match))
    g.add((matchURI, UO.hasHomeTeam, home_teamURI))
    g.add((matchURI, UO.hasAwayTeam, away_teamURI))

    # create TeamMatchStats instances
    home_team_statsURI = URIRef(UO+f"{home_team_code}TeamStats_{match_name}")
    away_team_statsURI = URIRef(UO+f"{away_team_code}TeamStats_{match_name}")
    g.add((home_team_statsURI, RDF.type, UO.TeamMatchStats))
    g.add((away_team_statsURI, RDF.type, UO.TeamMatchStats))
    g.add((home_team_statsURI, UO.statsOfTeam, home_teamURI))
    g.add((away_team_statsURI, UO.statsOfTeam, away_teamURI))
    
    # add stats to TeamMathStats for both and away teams
    # goals scored
    g.add((home_team_statsURI, UO.teamGoalsScored, Literal(home_goals, datatype=XSD.integer)))
    g.add((away_team_statsURI, UO.teamGoalsScored, Literal(away_goals, datatype=XSD.integer)))
    # ball possession
    g.add((home_team_statsURI, UO.ballPossession, Literal(possesion_home, datatype=XSD.float)))
    g.add((away_team_statsURI, UO.ballPossession, Literal(possesion_away, datatype=XSD.float)))
    # total shots
    g.add((home_team_statsURI, UO.teamTotalShots, Literal(total_shots_home, datatype=XSD.integer)))
    g.add((away_team_statsURI, UO.teamTotalShots, Literal(total_shots_away, datatype=XSD.integer)))
    # shots on target
    g.add((home_team_statsURI, UO.teamShotsOnTarget, Literal(on_target_home, datatype=XSD.integer)))
    g.add((away_team_statsURI, UO.teamShotsOnTarget, Literal(on_target_away, datatype=XSD.integer)))
    # corners
    g.add((home_team_statsURI, UO.corners, Literal(corners_home, datatype=XSD.integer)))
    g.add((away_team_statsURI, UO.corners, Literal(corners_away, datatype=XSD.integer)))
    # offsides
    g.add((home_team_statsURI, UO.teamOffsides, Literal(offsides_home, datatype=XSD.integer)))
    g.add((away_team_statsURI, UO.teamOffsides, Literal(offsides_away, datatype=XSD.integer)))
    # aerial duels won
    g.add((home_team_statsURI, UO.aerialDuelsWon, Literal(aerial_duels_home, datatype=XSD.float)))
    g.add((away_team_statsURI, UO.aerialDuelsWon, Literal(aerial_duels_away, datatype=XSD.float)))
    # saves
    g.add((home_team_statsURI, UO.totalSaves, Literal(saves_home, datatype=XSD.integer)))
    g.add((away_team_statsURI, UO.totalSaves, Literal(saves_away, datatype=XSD.integer)))
    # fouls commited
    g.add((home_team_statsURI, UO.teamFoulsCommitted, Literal(fouls_commited_home, datatype=XSD.integer)))
    g.add((away_team_statsURI, UO.teamFoulsCommitted, Literal(fouls_commited_away, datatype=XSD.integer)))
    # fouls won
    g.add((home_team_statsURI, UO.teamFoulsWon, Literal(fouls_won_home, datatype=XSD.integer)))
    g.add((away_team_statsURI, UO.teamFoulsWon, Literal(fouls_won_away, datatype=XSD.integer)))
    # yellow cards
    g.add((home_team_statsURI, UO.teamYellowCards, Literal(yellow_cards_home, datatype=XSD.integer)))
    g.add((away_team_statsURI, UO.teamYellowCards, Literal(yellow_cards_away, datatype=XSD.integer)))


    # Player data
    home_players = match_data["home_team_players"]
    away_players = match_data["away_team_players"]
    all_players = {}
    all_goals = []
    
    # find players in graphDB and get their URIs
    # if not found, add to unfound_players list
    unfound_players = []
    for player_name, pdata in home_players.items():
        
        # calculare minutes played, if 0 continue
        player_started = pdata["started"] 
        player_subbed_on = pdata["subbed_on"]
        player_subbed_off = pdata["subbed_off"]
        # minutes played
        minuted_played = calculate_minutes_played(player_started, player_subbed_on, player_subbed_off)
        #if minuted_played == 0:
        #    continue
        playerURI = find_player(player_name, home_team)
        if playerURI is None:
            unfound_players.append(player_name)
            continue
        all_players[playerURI] = pdata
        player_goals = pdata["goals"]
        for goal in player_goals:
            all_goals.append(goal)
 
    for player_name, pdata in away_players.items():
        
        # calculare minutes played, if 0 continue
        player_started = pdata["started"] 
        player_subbed_on = pdata["subbed_on"]
        player_subbed_off = pdata["subbed_off"]
        # minutes played
        minuted_played = calculate_minutes_played(player_started, player_subbed_on, player_subbed_off)
        #if minuted_played == 0:
        #    continue

        playerURI = find_player(player_name, away_team)
        if playerURI is None:
            unfound_players.append(player_name)

            continue
        all_players[playerURI] = pdata
        player_goals = pdata["goals"]
        for goal in player_goals:
            all_goals.append(goal)
    
    # sort goals by time, to find order
    goals_sorted = sorted([g[0] for g in all_goals])
    

    for playerURI, pdata in all_players.items():
        # create playerMatchStats instance
        # add player stats
        player_name = playerURI.split('#')[-1]
        playerStatsURI = URIRef(UO + f"{player_name}Stats_{match_name}")
        g.add((playerStatsURI, RDF.type, UO.PlayerMatchStats))
        g.add((playerStatsURI, UO.matchStatsOfPlayer, URIRef(playerURI)))
        g.add((playerStatsURI, UO.playerStatsOfMatch, matchURI))
        
        # calculate minutes played
        player_started = pdata["started"]
        player_subbed_on = pdata["subbed_on"]
        player_subbed_off = pdata["subbed_off"]
        minuted_played = calculate_minutes_played(player_started, player_subbed_on, player_subbed_off)
        g.add((playerStatsURI, UO.minutesPlayed, Literal(minuted_played, datatype=XSD.integer)))
        
        # goals
        goals = pdata["goals"]
        # for every goal create a Goal instance and link it to the playerMatchStats instance
        for goal in goals:
            goal_time = goal[0]
            # find goal order
            order = find_goal_order(goals_sorted, goal_time)
            goal_URI = URIRef(UO + f"Goal_{match_name}_{player_name}_{goal_time}")
            g.add((goal_URI, RDF.type, UO.Goal))
            g.add((goal_URI, UO.goalTime, Literal(goal_time, datatype=XSD.string)))
            g.add((goal_URI, UO.goalOrderInMatch, Literal(order, datatype=XSD.integer)))
            # check if penalty or own goal
            if goal[1]:
                if goal[1] == "pen":
                    g.add((goal_URI, UO.isPenaltyGoal, Literal(True, datatype=XSD.boolean)))
                elif goal[1] == "og":
                    g.add((goal_URI, UO.isOwnGoal, Literal(True, datatype=XSD.boolean)))
            # link goal to playerMatchStats
            g.add((playerStatsURI, UO.playerScored, goal_URI))
            # find assist for this goal and create Assist instance
            assistPlayerURI = find_assist(goal_time, all_players)
            print(f"Goal at {goal_time} by {player_name} assisted by {assistPlayerURI}")
            if assistPlayerURI:
                # create Assist instance and append properties
                assistURI = URIRef(UO + f"Assist_{match_name}_{assistPlayerURI.split('#')[-1]}_{goal_time}")
                g.add((assistURI, RDF.type, UO.Assist))
                g.add((assistURI, UO.assistTime, Literal(goal_time, datatype=XSD.string)))
                g.add((assistURI, UO.assistForGoal, goal_URI))
        
        # assists        
        assists = pdata["assists"]
        for assist in assists:
            # only append the player who assisted since everything else is appended when adding goals
            assistURI = URIRef(UO + f"Assist_{match_name}_{player_name}_{assist}")
            g.add((playerStatsURI, UO.playerAssisted, assistURI))
        
        # yellow cards
        yellow_cards = pdata["yellow_cards"]
        if yellow_cards:
            for yc in yellow_cards:
                yello_card = URIRef(UO + f"YellowCard_{match_name}_{player_name}_{yc}")
                g.add((yello_card, RDF.type, UO.YellowCard))
                g.add((yello_card, UO.yellowCardTime, Literal(yc, datatype=XSD.string)))
                g.add((playerStatsURI, UO.playerReceivedYellowCard, yello_card))
        # read cards
        red_card = pdata["red_cards"]
        if red_card:
            red_card_URI = URIRef(UO + f"RedCard_{match_name}_{player_name}")
            g.add((red_card_URI, RDF.type, UO.RedCard))
            g.add((red_card_URI, UO.redCardTime, Literal(red_card, datatype=XSD.string)))
            g.add((playerStatsURI, UO.playerReceivedRedCard, red_card_URI))
  
    print("Unfound players:", unfound_players)
    with open("Data/unfound_players2.txt", "a") as fp:
        for p in unfound_players:
            fp.write(p + "\n")
        fp.close()
    g.serialize(destination=f"Data/Matches/{match_name}.ttl", format='turtle')
    
    return

if __name__ == "__main__":
    #add_team_data()
    #add_players("Wolverhampton_Wanderers")\
    #add_match_data("Data/Matches/MCI_vs_BUR_PL25.json")
    add_match_data("Data/Matches/BHA_vs_FUL_PL25.json")
    
    pass