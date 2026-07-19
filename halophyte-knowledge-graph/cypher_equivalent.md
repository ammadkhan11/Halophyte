# From this prototype to a real Neo4j deployment

`build_graph.py` builds a plain JSON graph (`graph.json`) rather than writing
to a live Neo4j instance, because this sandbox has no database server and no
network access to one. The node/edge/property model is deliberately
Neo4j-shaped though, so moving to a real deployment is a translation, not a
redesign.

## Loading graph.json into Neo4j

```python
from neo4j import GraphDatabase
import json

graph = json.load(open("graph.json"))
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    for n in graph["nodes"]:
        session.run(
            f"MERGE (x:{n['kind']} {{id: $id}}) SET x += $props",
            id=n["id"], props={k: v for k, v in n.items() if k not in ("id", "kind")}
        )
    for e in graph["edges"]:
        session.run(
            f"""
            MATCH (a {{id: $src}}), (b {{id: $dst}})
            MERGE (a)-[r:{e['rel']} {{paper: $paper}}]->(b)
            SET r += $props
            """,
            src=e["source"], dst=e["target"], paper=e["paper"], props=e["props"]
        )
```

## Example Cypher queries this graph supports

**Missing-link detection** (species sharing mechanisms/genes but never co-cited):
```cypher
MATCH (a:Species)-[:HAS_MECHANISM|EXPRESSES_GENE]->(shared)<-[:HAS_MECHANISM|EXPRESSES_GENE]-(b:Species)
WHERE a.id < b.id
WITH a, b, collect(DISTINCT shared.name) AS sharedTraits, count(DISTINCT shared) AS n
WHERE n >= 3
  AND NOT EXISTS {
    MATCH (a)<-[:CITED_IN]-(p:Paper)-[:CITED_IN]->(b)
  }
RETURN a.name, b.name, sharedTraits, n
ORDER BY n DESC
```

**Underconnected species:**
```cypher
MATCH (s:Species)
OPTIONAL MATCH (s)-[r]-()
RETURN s.name, count(r) AS degree
ORDER BY degree ASC
LIMIT 10
```

**Mechanisms with sparse crop coverage:**
```cypher
MATCH (m:Mechanism)<-[:HAS_MECHANISM]-(s:Species)
WITH m, collect(DISTINCT s) AS species
UNWIND species AS sp
OPTIONAL MATCH (sp)-[:USED_FOR]->(app:Application)
WHERE app.name IN ["Oilseed crop","Food crop","Fodder","Seawater agriculture","Crop-improvement gene donor"]
RETURN m.name, size(species) AS nSpecies, count(DISTINCT sp) AS nCropLinked
ORDER BY toFloat(nCropLinked)/nSpecies ASC
```

**Node2Vec / graph embeddings** (Phase 3, item 4 in the project plan) --
once the graph is large enough to be worth it, the standard route is the
Neo4j Graph Data Science library:
```cypher
CALL gds.graph.project('halograph', ['Species','Gene','Mechanism'], '*')
CALL gds.node2vec.write('halograph', {embeddingDimension: 64, writeProperty: 'embedding'})
```
Then nearest-neighbor search over the `embedding` property gives you "find
species similar to X in mechanism-profile" without needing exact keyword
matches -- not implemented in this prototype since 31 papers is too small a
corpus for embeddings to be meaningful yet.

## Scaling the corpus (Phases 1-2)

This prototype's corpus (31 hand-picked, hand-extracted papers) stands in
for what the full project plan describes as an automated pipeline over
thousands of PubMed/PMC abstracts. To actually scale it up:

1. Swap `papers.py`'s hand-written list for a script that queries the NCBI
   E-utilities API (`Bio.Entrez` in Biopython) for the search terms in the
   project brief, and stores raw abstracts + metadata in SQLite.
2. Replace my by-hand entity extraction with a batched LLM extraction step:
   call the Claude API once per abstract with a fixed JSON-schema prompt
   (the schema is already defined by `add_node`'s node kinds), and merge
   results the same way `build_graph.py` currently merges my hand-picked
   entities.
3. Add the entity-normalization step described in the project's Phase 2
   (GBIF backbone for species names, UniProt/NCBI Gene for gene names) --
   this prototype skipped it because with 31 papers I could normalize names
   by eye (e.g. recognizing `SsHKT1;1` and `HKT1` as the same gene family).
   At thousands-of-papers scale this step is not optional.
4. Everything downstream -- `build_graph.py`, `gap_analysis.py`, and the
   app's graph/query/hypotheses tabs -- takes a bigger `graph.json` as-is;
   none of it assumes a 31-paper corpus except the "keep it under ~180
   words, cite paper ids" system prompt in the query tab, which would need
   to switch from full-corpus-in-context to real vector retrieval once the
   corpus no longer fits in a single prompt.
