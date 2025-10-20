from unidecode import unidecode
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from unidecode import unidecode

def main():
    """
    Script to add clean skos:altLabels to Player entities e.g. for Martin Ødegaard add skos:altLabel Martin Odegaard
    """
    repo_url = "http://localhost:7200/repositories/UnitedApp"
    update_url = f"{repo_url}/statements"

    # Step 1: Fetch players with non-ASCII labels
    sparql = SPARQLWrapper(repo_url)
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
    PREFIX : <http://semanticweb.org/unitedOntology#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?player ?label
    WHERE {
    ?player a :Player ;
            rdfs:label ?label .
    FILTER(REGEX(STR(?label), "[^\\\\x00-\\\\x7F]"))
    }
    """)
    results = sparql.query().convert()

    # Step 2: Generate and insert altLabels
    update = SPARQLWrapper(update_url)
    update.setMethod(POST)

    for r in results["results"]["bindings"]:
        uri = r["player"]["value"]
        label = r["label"]["value"]
        print(uri, label)
        alt_label = unidecode(label)
        print(alt_label)
        q = f"""
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        INSERT DATA {{
        <{uri}> skos:altLabel "{alt_label}"@en .
        }}
        """
        update.setQuery(q)
        update.query()


if __name__ == "__main__":
    main()