"""
Phase 5 -- Hypothesis Generation via Graph Analysis.

Three structural checks, run directly on graph.json:
1. Missing-link detection: species pairs sharing >=2 mechanisms/genes
   but never mentioned together in the same paper.
2. Underconnected nodes: species with few edges relative to the rest
   of the graph.
3. Mechanism clusters with sparse crop/application coverage: mechanisms
   well-connected to species but rarely linked to a food/fodder/crop
   type application.
"""
import json
from itertools import combinations
from collections import defaultdict

graph = json.load(open("graph.json"))
nodes = {n["id"]: n for n in graph["nodes"]}
edges = graph["edges"]

species_ids = [n["id"] for n in graph["nodes"] if n["kind"] == "Species"]

# species -> set of (mechanism/gene) node ids it's linked to
profile = defaultdict(set)
# species -> set of paper ids that mention it
species_papers = defaultdict(set)

for e in edges:
    if e["rel"] in ("HAS_MECHANISM", "EXPRESSES_GENE") and e["source"] in species_ids:
        profile[e["source"]].add(e["target"])
    if e["rel"] == "CITED_IN" and e["target"] in species_ids:
        species_papers[e["target"]].add(e["paper"])

print("=== 1. Missing-link candidates (shared profile, never co-cited) ===")
found = 0
for a, b in combinations(species_ids, 2):
    shared = profile[a] & profile[b]
    if len(shared) >= 2 and not (species_papers[a] & species_papers[b]):
        shared_names = [nodes[s]["name"] for s in shared]
        print(f"- {nodes[a]['name']} <-> {nodes[b]['name']}: share {shared_names}")
        found += 1
print(f"({found} candidate pairs)\n")

print("=== 2. Underconnected species (degree <= 2) ===")
degree = defaultdict(int)
for e in edges:
    degree[e["source"]] += 1
    degree[e["target"]] += 1
under = sorted(
    [(nodes[s]["name"], degree[s]) for s in species_ids],
    key=lambda x: x[1]
)
for name, d in under[:8]:
    print(f"- {name}: degree {d}")
print()

print("=== 3. Mechanisms with sparse crop/application coverage ===")
mech_ids = [n["id"] for n in graph["nodes"] if n["kind"] == "Mechanism"]
crop_apps = {"Oilseed crop", "Food crop", "Fodder", "Seawater agriculture", "Crop-improvement gene donor"}
for m in mech_ids:
    linked_species = {e["source"] for e in edges if e["rel"] == "HAS_MECHANISM" and e["target"] == m}
    n_species = len(linked_species)
    # does any of those species have a USED_FOR edge into a crop-type application?
    crop_linked = set()
    for e in edges:
        if e["rel"] == "USED_FOR" and e["source"] in linked_species and nodes[e["target"]]["name"] in crop_apps:
            crop_linked.add(e["source"])
    print(f"- {nodes[m]['name']}: {n_species} species studied, {len(crop_linked)} with crop/application link")
