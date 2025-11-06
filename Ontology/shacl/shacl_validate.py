from pyshacl import validate

def shacl_validate(ont_graph, shapes,data_graph):
    conforms, _, results_text = validate(
    data_graph=data_graph,
    shacl_graph=shapes,
    ont_graph=ont_graph,
    inference ="rdfs",
    )

    return conforms, results_text

if __name__ == "__main__":
    ont_graph = "ontology_export.ttl"
    shapes = "shacl/shapes.ttl"
    data_graph = "Data/Matches/1/ttls/BHA_vs_FUL_PL25.ttl"
    shacl_validate(ont_graph, shapes,data_graph)
