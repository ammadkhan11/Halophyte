"""
Phase 3 -- Graph Construction.

Turns the paper corpus (papers.py) into a node/edge graph matching the
schema in the project brief:

Node types: Species, Gene, Mechanism, Geography, Application, Paper
Edge types: HAS_MECHANISM, EXPRESSES_GENE, FOUND_IN, USED_FOR,
            TOLERATES_UP_TO, CITED_IN (paper -> entity provenance)

This is a from-scratch Python/JSON graph rather than a live Neo4j
instance (no Neo4j server available in this environment), but the
node/edge/property model is deliberately Neo4j-shaped -- see
scripts/cypher_equivalent.md for the Cypher this would become on a
real Neo4j deployment.
"""
import json
from papers import PAPERS

nodes = {}   # id -> node dict
edges = []   # list of edge dicts


def node_id(kind, name):
    return f"{kind}:{name}"


def add_node(kind, name):
    nid = node_id(kind, name)
    if nid not in nodes:
        nodes[nid] = {"id": nid, "kind": kind, "name": name}
    return nid


def add_edge(src, rel, dst, paper_id, props=None):
    edges.append({
        "source": src, "target": dst, "rel": rel,
        "paper": paper_id, "props": props or {}
    })


for p in PAPERS:
    paper_nid = add_node("Paper", p["id"])
    nodes[paper_nid].update({
        "title": p["title"], "authors": p["authors"], "year": p["year"],
        "journal": p["journal"], "url": p["url"], "summary": p["summary"],
    })

    for sp in p["species"]:
        sp_nid = add_node("Species", sp)
        add_edge(paper_nid, "CITED_IN", sp_nid, p["id"])

        for mech in p["mechanisms"]:
            m_nid = add_node("Mechanism", mech)
            add_edge(sp_nid, "HAS_MECHANISM", m_nid, p["id"])

        for gene, ortholog in p["genes"]:
            g_nid = add_node("Gene", gene)
            add_edge(sp_nid, "EXPRESSES_GENE", g_nid, p["id"],
                      {"ortholog_name": ortholog} if ortholog else {})

        for geo in p["geography"]:
            geo_nid = add_node("Geography", geo)
            add_edge(sp_nid, "FOUND_IN", geo_nid, p["id"])

        for app in p["applications"]:
            app_nid = add_node("Application", app)
            add_edge(sp_nid, "USED_FOR", app_nid, p["id"])

        if p["salinity"] and p["salinity"].get("value_mM") is not None:
            add_edge(sp_nid, "TOLERATES_UP_TO", sp_nid, p["id"],
                      {"value_mM": p["salinity"]["value_mM"],
                       "note": p["salinity"].get("note", "")})

    # genes/mechanisms mentioned with no specific species (e.g. review papers)
    if not p["species"]:
        for gene, ortholog in p["genes"]:
            g_nid = add_node("Gene", gene)
            add_edge(paper_nid, "CITED_IN", g_nid, p["id"])
        for mech in p["mechanisms"]:
            m_nid = add_node("Mechanism", mech)
            add_edge(paper_nid, "CITED_IN", m_nid, p["id"])

# de-dupe identical edges (same source/rel/target/paper), merge props
seen = {}
deduped = []
for e in edges:
    key = (e["source"], e["rel"], e["target"], e["paper"])
    if key not in seen:
        seen[key] = e
        deduped.append(e)
edges = deduped

graph = {"nodes": list(nodes.values()), "edges": edges}

with open("graph.json", "w", encoding="utf-8") as f:
    json.dump(graph, f, ensure_ascii=False, indent=None, separators=(",", ":"))

print(f"{len(nodes)} nodes, {len(edges)} edges")
kinds = {}
for n in nodes.values():
    kinds[n["kind"]] = kinds.get(n["kind"], 0) + 1
print(kinds)
