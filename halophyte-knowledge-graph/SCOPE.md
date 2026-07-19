# Scope: what's real, what's simplified

Being direct about this so it's usable as an honest starting point rather
than something that looks more finished than it is.

## Real

- **Every paper is real.** All 31 entries in `data/papers.py` are actual
  papers/sources found via web search, with real titles, authors, years,
  journals and working source URLs — nothing fabricated or simulated.
- **Every entity extraction is grounded.** Species, genes, mechanisms,
  geography, and application tags were pulled from each paper's actual
  abstract/summary content, by hand, checked against the source, not
  guessed or hallucinated. Summaries are paraphrased in my own words, never
  quoted verbatim (copyright).
- **The graph structure is real and queryable** — 74 nodes, 164 edges, all
  traceable back to a specific paper via the `paper` field on every edge
  (the "provenance node" idea from the project brief, implemented as an
  edge property rather than a separate traversal hop — functionally
  equivalent, simpler to query at this scale).
- **The "Ask a Question" tab makes a real LLM call.** It's not a canned
  response — it sends your question plus the full corpus to the live
  Claude API and returns a genuinely generated, citation-constrained answer.
- **The three Phase-5 gap-analysis algorithms are real code**, not
  pre-written example output — run `scripts/gap_analysis.py` yourself, or
  watch the "Research Opportunities" tab recompute them live in the browser.

## Simplified from the full project plan

- **Corpus size:** 31 papers, not "a few thousand to tens of thousands."
  This was the deliberate trade-off to keep everything hand-verifiable in
  one sitting rather than trusting an unreviewed automated pipeline. The
  gap-analysis results are correspondingly modest — with a real
  thousands-of-papers corpus, missing-link and underconnected-species
  results would be far richer and more surprising than what a 31-paper
  graph can show.
- **No live PubMed/PMC/bioRxiv API pipeline.** The brief's Phase 1 describes
  querying NCBI E-utilities and preprint APIs automatically; I gathered this
  corpus via web search instead, since this sandbox doesn't have network
  access to NCBI's API. `cypher_equivalent.md` has the actual `Bio.Entrez`
  code to add this back in.
- **No entity normalization step (GBIF/UniProt).** With 31 papers I could
  eyeball that `SsHKT1;1`, `HKT1`, and "the HKT-type transporter" are the
  same gene family. At real scale this needs the taxonomic/gene-name
  normalization the brief calls for in Phase 2 — skipping it there would
  silently fragment the graph (e.g. "S. europaea" and "Salicornia europaea"
  becoming two different nodes).
- **No Neo4j server.** The graph lives as JSON (`graph.json`), not in an
  actual Neo4j instance, because this sandbox has no database server and no
  network route to one. The data model is Neo4j-shaped on purpose --
  see `cypher_equivalent.md` for the load script and equivalent Cypher.
- **No graph embeddings / Node2Vec.** Not meaningful yet at 31 papers --
  noted in `cypher_equivalent.md` for when the corpus is big enough to
  justify it.
- **RAG is "whole corpus in context," not real retrieval.** At 31 papers,
  the full corpus fits comfortably in one prompt, so there's no vector
  index or retrieval step — the LLM just reads everything each time. This
  stops scaling somewhere in the low hundreds of papers; past that you'd
  need actual embedding-based retrieval (see `cypher_equivalent.md`).

## Bottom line

Everything you can click on is real: real papers, real extracted facts,
real graph, real live model call, real gap-detection code. What's scaled
down is breadth (31 papers instead of thousands) and the automation of
getting there (hand-curated instead of a Entrez+LLM-batch pipeline) --
both addressed concretely in `cypher_equivalent.md` if you want to grow
this into the full version.
