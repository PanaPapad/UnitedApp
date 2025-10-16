from rdflib import *
from SPARQLWrapper import SPARQLWrapper, JSON
import requests
import datetime
import time
import os
from populate import post_toGraphDB

GRAPHDB_ENDPOINT = "http://localhost:7200/repositories/UnitedApp"


def export_repo(format: str = "ttl"):
    """
    Exports all triples from the KG and saves them in the chosen RDF format.

    Supported formats:
      - ttl       → text/turtle
      - rdfxml    → application/rdf+xml
      - ntriples  → application/n-triples
      - jsonld    → application/ld+json

    Returns:
        The path to the exported file.
    """
    format_map = {
        "ttl": "text/turtle",
        "rdfxml": "application/rdf+xml",
        "ntriples": "application/n-triples",
        "jsonld": "application/ld+json"
    }

    if format not in format_map:
        raise ValueError(f"Unsupported format '{format}'. Supported formats: {list(format_map.keys())}")

    headers = {
        "Accept": format_map[format]
    }

    response = requests.get(f"{GRAPHDB_ENDPOINT}/statements", headers=headers)

    current_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    os.makedirs("ExportedRepos", exist_ok=True)
    file_path = f"ExportedRepos/repo_{current_time}.{format}"

    if response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Repository exported successfully to {file_path}")
    else:
        print(f"Failed to export: {response.status_code} - {response.text}")

    return file_path

def enrichStadiums():
    """
    Function that queries wikidata using the rdf label of each stadium and enriches them with info about image and creationDate
    """
    # load existing repo and the ontology in the graph
    repo = export_repo()
    g = Graph()
    g.parse("unitedOntology.owl",format="xml")
    g.parse(repo, format="turtle")

    UO = Namespace("http://semanticweb.org/unitedOntology#")
    g.bind("uo", UO)
    
    # define the wikidata endpoint
    endpoint =SPARQLWrapper("https://query.wikidata.org/sparql")
    
    # for every stadium create a query using the label
    for stadium in g.subjects(RDF.type, UO.Stadium):
        for label in g.objects(stadium, RDFS.label):
            label = label.strip()
            if label == "City of Manchester Stadium":
                label = "Etihad Stadium"
            if label == "Falmer Stadium":
                label = "Brighton Community Stadium"
            if label == "St James' Park":
                label="St James’ Park"
            query = """
            SELECT ?stadium ?image ?date WHERE {{
                ?stadium rdfs:label "{label}"@en.
                OPTIONAL{{?stadium wdt:P31 wd:Q1154710}}.
                ?stadium wdt:P18 ?image.
                ?stadium wdt:P1619 ?date
                }} LIMIT 1
            """.format(label=label)

            endpoint.setQuery(query)
            endpoint.setReturnFormat(JSON)
            results = endpoint.query().convert()
            # add properties to the graph
            print(f"Info about stadium {label}")
            for result in results["results"]["bindings"]:
                pic = result["image"]["value"]
                creationDate = result["date"]["value"]
                print(stadium,pic,creationDate)
                g.add((stadium, UO.hasPictureURL, Literal(pic,datatype=XSD.string)))
                g.add((stadium, UO.creationDate, Literal(creationDate,datatype=XSD.string)))

    # serialize and post to graphDB
    rdf_data = g.serialize(format='turtle')
    post_toGraphDB(rdf_data)
    return

def get_players_of_team(team_label):
    """
    Function that queries graphdb and returns a tuple of:
    player_label, playerURI
    """
    endpoint = SPARQLWrapper(GRAPHDB_ENDPOINT)
    query= """
        PREFIX : <http://semanticweb.org/unitedOntology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?player_label ?player WHERE{{
            ?player :playsFor ?team .
            ?player rdfs:label ?player_label .
            ?team rdfs:label "{team_label}".
        }}

        """.format(team_label=team_label)
    endpoint.setQuery(query)
    endpoint.setReturnFormat(JSON)
    results = endpoint.query().convert()
    players = []
    for result in results["results"]["bindings"]:
        #players[result["player_label"]["value"]] = result["player"]["value"] 
        players.append((result["player_label"]["value"],result["player"]["value"]))
    return players

def get_team_labels():
    endpoint = SPARQLWrapper(GRAPHDB_ENDPOINT)
    query= """
        PREFIX : <http://semanticweb.org/unitedOntology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?team_label WHERE{{
            ?t a :Team.
            ?t rdfs:label ?team_label  
        }}
        """
    endpoint.setQuery(query)
    endpoint.setReturnFormat(JSON)
    results = endpoint.query().convert()
    
    teams=[]
    for t in results["results"]["bindings"]:
        teams.append(t["team_label"]["value"])
    
    return teams

def safe_query(endpoint, query, retries=5):
    """Run SPARQL query safely with retry and backoff."""
    delay = 5
    for _ in range(retries):
        try:
            endpoint.setQuery(query)
            endpoint.setReturnFormat(JSON)
            return endpoint.query().convert()
        except Exception as e:
            if "429" in str(e):
                print(f"⚠️ Rate limit hit. Waiting {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
    print("❌ Too many retries, skipping this query.")
    return {"results": {"bindings": []}}

def batch(iterable, size=10):
    """Yield successive n-sized chunks from iterable."""
    iterable = list(iterable)
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

def find_wikidata_team(team_name):
    endpoint =SPARQLWrapper("https://query.wikidata.org/sparql")
    team_name+= " F.C."
    query= """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?team WHERE {{
            ?team rdfs:label "{team_name}"@en
        }} LIMIT 1
    """.format(team_name=team_name)
    endpoint.setQuery(query)
    endpoint.setReturnFormat(JSON)
    results = endpoint.query().convert()

    # Extract the QID (remove URI prefix)
    bindings = results["results"]["bindings"]
    if not bindings:
        return None  # no match found

    uri = bindings[0]["team"]["value"]
    qid = uri.split("/")[-1]  # take last part of the URI

    return qid

def enrichPlayers():
    
    #repo = export_repo()
    repo = "ExportedRepos/repo2025-10-08_15_03_00_170599.ttl"
    g = Graph()
    g.parse("unitedOntology.owl",format="xml")
    g.parse(repo, format="turtle")

    UO = Namespace("http://semanticweb.org/unitedOntology#")
    g.bind("uo", UO)
    
    endpoint =SPARQLWrapper("https://query.wikidata.org/sparql")
    # find all teams and the players of each team
    team_labels = get_team_labels()
    #team_labels = ["Manchester United"]
    unwanted_players = []
    for team in team_labels:
        players = get_players_of_team(team)
        
        wikidata_team = find_wikidata_team(team)
        for batch_players in batch(players, size=10):

            if not batch_players:
                continue

            safe_labels = []
            for label, _ in batch_players:
                escaped = label.replace('"', '\\"')
                safe_labels.append(f'"{escaped}"@en')
            values_clause = " ".join(safe_labels)
            if not values_clause:
                print("⚠️ Skipping empty VALUES clause")
                continue
        
            print(values_clause)

            query="""
            SELECT ?player ?label ?dob ?height ?weight ?image WHERE {{
            VALUES ?label {{ {labels} }}
            ?player rdfs:label ?label. 
            ?player wdt:P106 wd:Q937857. # occupation -> footballer
            ?player wdt:P569 ?dob .
            ?player wdt:P54 wd:{wikidata_team} .
            OPTIONAL {{ ?player wdt:P2048 ?height . }}
            OPTIONAL {{ ?player wdt:P2067 ?weight . }}
            OPTIONAL {{ ?player wdt:P18 ?image . }}
            }} 
            
            """.format(labels=values_clause, wikidata_team=wikidata_team)
            endpoint.setQuery(query)
            endpoint.setReturnFormat(JSON)

            results = safe_query(endpoint, query)
            players = []
            for result in results["results"]["bindings"]:
                label = result["label"]["value"]
                for l, p in batch_players:
                    if l == label:
                        print(label)
                        player = URIRef(p)
                        batch_players.remove((l,p))
                if player is None:
                    continue
                if "dob" in result:
                    birthday = result["dob"]["value"]
                    print(birthday)
                    g.add((player, UO.hasBirthDate, Literal(birthday, datatype=XSD.string)))
                if "height" in result:
                    height = result["height"]["value"]
                    g.add((player,UO.hasHeight,Literal(height, datatype=XSD.float)))
                    print(height)
                if 'weight' in result:
                    weight = result["weight"]["value"]
                    g.add((player,UO.hasWeight,Literal(weight, datatype=XSD.float)))
                    print(weight)
                if 'image' in result:
                    image = result["image"]["value"]
                    g.add((player,UO.hasPictureURL,Literal(image, datatype=XSD.string)))
                    print(image)
            print("Batch players left: ", batch_players)
            for l,_ in batch_players:
                unwanted_players.append(l)
            print(unwanted_players)

        print("Unwanted Players", unwanted_players)
            
    rdf_data = g.serialize(format='turtle')
    post_toGraphDB(rdf_data)
    file = open('unwanted_players.txt','a')
    print("Length of ynwanted players:", len(unwanted_players))
    for p in unwanted_players:
	    file.write(p+"\n")     

if __name__ == "__main__":
    #enrichPlayers()
    pass