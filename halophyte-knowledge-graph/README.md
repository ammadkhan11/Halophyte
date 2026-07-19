# Halophyte Knowledge Graph — a working prototype of Project 4

This is a real, working implementation of the plan in
`Project4_Halophyte_Knowledge_Graph.md` — scaled down to a corpus I could
realistically gather and hand-verify in one sitting (31 real papers, found
via web search, not simulated), rather than the full multi-week /
thousands-of-papers pipeline the plan describes. Read `SCOPE.md` for exactly
what's real vs. simplified, and `cypher_equivalent.md` for how to grow this
into the full pipeline on real Neo4j infrastructure.

```
halophyte-knowledge-graph/
├── app/
│   └── halophyte_knowledge_graph.html   ← the working app (self-contained)
├── data/
│   ├── papers.py                        ← the 31-paper corpus + hand-extracted entities
│   ├── graph.json                       ← constructed graph (nodes + edges + provenance)
│   └── kg_data.json                     ← graph.json + paper metadata, bundled (what the app embeds)
├── scripts/
│   ├── build_graph.py                   ← Phase 3: corpus → graph.json
│   └── gap_analysis.py                  ← Phase 5: hypothesis generation, Python prototype of the app's JS
├── design-system/                       ← same design system as the companion halophyte-database project
├── cypher_equivalent.md                 ← how this becomes real Neo4j + Cypher at scale
└── SCOPE.md                             ← what's real, what's simplified, and why
```

## What the app actually does

- **Graph Explorer** — force-directed graph of 74 nodes (17 species, 7
  genes, 7 mechanisms, 4 geographies, 8 applications, 31 papers) and 164
  edges, all sourced from real papers. Click any node for its connections
  and the papers backing each one, with a link out to the original source.
- **Ask a Question** — a real Retrieval-Augmented-Generation query: your
  question plus the full paper corpus is sent live to the Claude API
  (`api.anthropic.com`, via the same in-artifact API access used in
  Claude.ai), with a system prompt that requires citing paper IDs and
  forbids answering from outside knowledge. This is genuinely LLM-powered,
  not a canned response.
- **Research Opportunities** — three graph-gap algorithms (ported from
  `gap_analysis.py`, running live in the browser): missing-link candidates,
  underconnected species, and mechanisms with sparse crop-application
  coverage. Exactly the three analyses named in the project brief's Phase 5.
- **Corpus** — the full reading list behind the graph, each entry linking to
  its real source.

## Running it

`app/halophyte_knowledge_graph.html` is self-contained (data embedded,
D3 loaded from a CDN for the graph layout) — open it in a browser. The
"Ask a Question" tab needs to be run inside Claude.ai (or wherever the
`api.anthropic.com` call is proxied) to actually reach the model; outside
that context the fetch will fail, which the UI reports rather than hangs on.

## Regenerating the graph after editing the corpus

```
python3 scripts/build_graph.py     # papers.py -> data/graph.json
```
Then re-bundle `graph.json` with the paper metadata into `kg_data.json` and
re-embed it in the HTML (same pattern as the halophyte-database project's
`clean_data.py` → embed step).

## Design

Same visual system as the companion halophyte-database project
(`design-system/`), extended with a node-color scheme for the six graph
entity kinds — see `design-system/DESIGN_SYSTEM.md`'s existing writeup for
the rationale; the new kind-color choices follow the same "ground it in the
subject" method (species = the primary teal, since they're the graph's
main subject; genes = clay, the secondary accent; mechanisms get a new
slate-blue as the "engineering layer"; geography a sage green; application
keeps the mustard, since a use case is the "valuable, singular" endpoint of
a research thread, matching mustard's original single-highlight role).
