# Project 4: Halophyte Knowledge Graph from Scientific Literature
### LLM-Powered Text Mining & Hypothesis Generation for Salt-Tolerance Research

---

## 1. Problem Statement

Halophyte and saline-agriculture research is scattered across tens of thousands of papers spanning plant physiology, genomics, agronomy, and ecology — published over more than 50 years, across journals with no unified vocabulary or structured data format. A researcher trying to answer a question like "which species share mechanism X but have never been directly compared" or "which understudied species might tolerate salinity level Y based on their taxonomic relatives" has no good tool — they'd have to manually read hundreds of papers.

This project uses LLMs to text-mine this literature at scale, extract structured entities and relationships (species, genes, mechanisms, salinity thresholds, geography, applications), and assemble them into a queryable knowledge graph. The graph itself becomes a discovery tool: graph structure (missing links, clusters, isolated nodes) can surface research gaps and hypotheses a human would take months to notice by reading alone.

**Core question:** Can we build a structured, queryable knowledge graph of halophyte salt-tolerance research that both answers direct questions and actively surfaces understudied species/mechanism combinations worth investigating?

---

## 2. Objectives

- Extract entities and relationships from a large corpus of halophyte/salinity literature using LLMs.
- Build a graph database connecting species ↔ mechanisms ↔ genes ↔ geography ↔ applications.
- Build a natural-language query interface (RAG) over the graph.
- Use graph analysis to generate a ranked list of research-gap hypotheses.

---

## 3. Solution Methodology

### Phase 1 — Corpus Assembly
1. Query PubMed/PMC via the NCBI E-utilities API for papers matching terms like "halophyte," "salt tolerance," "salinity stress plant," "biosaline agriculture," combined with species names, gene family names, etc. Aim for a corpus of a few thousand to tens of thousands of abstracts (full text where openly available via PMC Open Access subset).
2. Supplement with bioRxiv/agriRxiv preprints (via their APIs) for more recent, less-indexed work.
3. Pull structured baseline data from **eHALOPH** (curated halophyte species database) to seed the graph with a validated species list and known tolerance traits — this gives you a ground-truth backbone to check LLM extraction quality against.
4. Store raw text + metadata (title, authors, year, journal, DOI) in a local database (SQLite or a simple document store) as the working corpus.

### Phase 2 — Entity & Relation Extraction (LLM-driven)
1. Define your target schema up front — this matters a lot for graph quality. Suggested entity types:
   - **Species** (halophyte or crop)
   - **Gene/Protein** (e.g., SOS1, NHX1, HKT1)
   - **Mechanism** (e.g., ion compartmentalization, osmotic adjustment, antioxidant response)
   - **Salinity threshold/tolerance level** (quantitative, e.g., "tolerates up to 20 dS/m")
   - **Geography/habitat** (e.g., "coastal salt marsh, Mediterranean")
   - **Application** (e.g., "food crop," "biofuel," "phytoremediation," "fodder")
2. Use an LLM (via API — Claude or similar) with a structured extraction prompt per abstract/paper: "Extract all instances of [schema] from this text, output as JSON." Batch this across the corpus.
3. Post-process: deduplicate entities (e.g., "Salicornia europaea" vs. "S. europaea" vs. common name), normalize using a taxonomic reference (GBIF taxonomic backbone is useful for species name normalization), and resolve gene names against UniProt/NCBI Gene naming conventions.
4. Quality-check a random sample of extractions manually against source text to estimate extraction accuracy before trusting the full graph.

### Phase 3 — Graph Construction
1. Load entities and relationships into a graph database — **Neo4j** (free community edition) is the standard choice, with Cypher as the query language.
2. Node types: Species, Gene, Mechanism, Geography, Application, Paper (as a provenance node, so every relationship can be traced back to its source).
3. Edge types: `HAS_MECHANISM`, `EXPRESSES_GENE`, `FOUND_IN`, `USED_FOR`, `TOLERATES_UP_TO` (with salinity value as an edge property), `CITED_IN`.
4. Compute graph embeddings (Node2Vec or a graph neural network embedding) to enable similarity search — "find species similar to X in mechanism-profile" becomes a nearest-neighbor query in embedding space rather than requiring exact keyword matches.

### Phase 4 — Natural Language Query Interface (RAG)
1. Build a retrieval-augmented generation system: user asks a question in plain English → system translates intent into a Cypher graph query (or retrieves relevant subgraph via embedding similarity) → relevant nodes/paths/paper snippets are passed to an LLM → LLM synthesizes a natural-language answer with citations back to source papers.
2. This lets a researcher ask things like "which halophyte species have been studied for vacuolar ion sequestration but not yet tested as candidates for gene transfer to wheat?" and get a grounded answer traceable to specific papers.

### Phase 5 — Hypothesis Generation via Graph Analysis
1. Run structural analysis on the graph to surface gaps:
   - **Missing-link detection:** species pairs that share many mechanism/gene connections but have never been directly co-studied or compared in any paper — strong candidates for a novel comparative study.
   - **Underconnected nodes:** species with very few extracted relationships despite being taxonomically close to well-studied, highly tolerant species — flags understudied species worth investigating.
   - **Mechanism clusters with sparse crop coverage:** mechanisms well-documented in halophytes but rarely mentioned in crop-improvement literature — flags translational gaps between basic and applied research.
2. Produce a ranked "research opportunity" report from this analysis — this is a genuinely useful, novel output that goes beyond just organizing existing information.

---

## 4. Datasets & Resources

| Resource | Purpose | Access |
|---|---|---|
| PubMed/PMC (via NCBI E-utilities API) | Primary literature corpus | ncbi.nlm.nih.gov/home/develop/api |
| PMC Open Access Subset | Full-text papers (not just abstracts) where license permits | ncbi.nlm.nih.gov/pmc/tools/openftlist |
| bioRxiv / agriRxiv APIs | Recent preprints | api.biorxiv.org |
| eHALOPH (Univ. of Sussex) | Curated halophyte species/traits database — ground-truth backbone | sussex.ac.uk (search "eHALOPH") |
| GBIF Taxonomic Backbone | Species name normalization/taxonomy | gbif.org |
| UniProt / NCBI Gene | Gene/protein name normalization | uniprot.org, ncbi.nlm.nih.gov/gene |
| CrossRef API | Paper metadata (DOIs, citation info) | api.crossref.org |

---

## 5. Tools & Tech Stack

- **Corpus retrieval:** Python (Biopython's `Entrez` module for PubMed API, `requests` for bioRxiv/CrossRef APIs)
- **LLM extraction:** Claude API (or similar) with structured JSON-mode prompting; batch processing for cost/time efficiency
- **Graph database:** Neo4j Community Edition + Cypher query language
- **Graph embeddings:** Node2Vec (via `node2vec` Python package) or a GNN framework (PyTorch Geometric) if going deeper
- **RAG layer:** LangChain or a custom retrieval pipeline combining Neo4j Cypher queries + vector similarity search + LLM synthesis
- **Front-end:** Streamlit chat-style interface, or a graph visualization front-end (Neo4j Bloom, or `pyvis`/`streamlit-agraph` for embedding graph views in a web app)

---

## 6. Suggested Timeline

| Weeks | Milestone |
|---|---|
| 1 | Corpus assembly (API pulls, storage setup) |
| 2–4 | LLM-based entity/relation extraction, schema iteration, quality checks |
| 5 | Entity normalization + deduplication |
| 6 | Graph construction in Neo4j, embeddings |
| 7 | RAG query interface build |
| 8 | Graph analysis for hypothesis generation, final report + demo |

---

## 7. Deliverables

1. Structured corpus (papers + extracted entities/relations, with provenance).
2. Populated Neo4j knowledge graph, queryable via Cypher.
3. Natural-language RAG query interface with citation-backed answers.
4. Ranked "research opportunity" report from graph gap analysis.
5. Written methodology document — this is genuinely publishable as a methods paper in a computational biology or bioinformatics venue if done rigorously.

---

## 8. Key Risks & Mitigations

- **Risk:** LLM extraction errors/hallucination (inventing relationships not actually in the text). **Mitigation:** always extract with direct text-span grounding (require the LLM to quote/point to the supporting sentence range internally, even if not shown to the end user) and manually spot-check a statistically meaningful sample (e.g., 100 random extractions) before trusting graph-wide conclusions.
- **Risk:** Entity normalization is messier than expected (synonyms, spelling variants, outdated taxonomy). **Mitigation:** budget real time for this — it's usually the most underestimated step in any text-mining project; lean on GBIF/UniProt canonical IDs rather than free-text matching wherever possible.
- **Risk:** Full-text access limits (many papers are paywalled, only abstracts available). **Mitigation:** design the extraction schema to work reasonably well from abstracts alone (they usually state key findings), and treat full-text PMC Open Access papers as a bonus higher-quality subset rather than a requirement.
