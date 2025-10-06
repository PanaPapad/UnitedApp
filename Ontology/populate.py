from rdflib import Graph, Namespace, RDF, URIRef, Literal
from rdflib.namespace import RDFS, DC, XSD
import requests
import pandas as pd



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

#add_team_data()
add_players("Wolverhampton_Wanderers")
