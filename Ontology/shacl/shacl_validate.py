
from pyshacl import validate

ont_graph = "ontology_export.ttl"
shapes = "shacl/shapes.ttl"
data_graph = "Data/sh_test.ttl"

conforms, _, results_text = validate(
    data_graph=data_graph,
    shacl_graph=shapes,
    ont_graph=ont_graph,
    inference ="rdfs",

    )
print(results_text)