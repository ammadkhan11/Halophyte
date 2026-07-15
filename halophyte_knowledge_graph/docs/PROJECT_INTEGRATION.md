# Integrating the Knowledge Graph into the Halophyte Project

## Final project structure

| Project phase | Existing contribution | New contribution from this module | Demonstrable output |
|---|---|---|---|
| Phase 1 — Grass dictionary | Searchable 30-grass master data: species, mechanism, GR50, Na+, Cl− and K+ shoot/root values | Imports species, mechanisms and GR50 values as a clearly labelled project-data backbone | Search one grass and inspect its structured traits |
| Phase 2 — ML prediction | Individual-grass and mechanism-group regression for missing ion values | Adds literature context and evidence to the selected species/mechanism; it does not replace a calculated prediction | Show calculated prediction, metrics, and connected evidence separately |
| Phase 3 — Analysis dashboard | Data exploration and model comparison | Adds evidence explorer, graph map, manual review queue and research-gap view | Filter a graph, open sources and display opportunity ranking |
| Phase 4 — Research knowledge graph | New | Reproducible literature pipeline: PubMed → extraction → review → graph → gaps | Citation-backed relationship and transparent research lead |

## Why this is a genuine extension

The dictionary answers: **what values are recorded for a grass?**

The predictor answers: **what values does the model estimate when data are missing?**

The knowledge graph answers: **what published mechanisms, genes, habitats and applications are connected to that grass, and what parts of the evidence network remain weak?**

This keeps the scientific distinction clear. A prediction is not represented as literature evidence, and a literature relationship is not treated as a model prediction.

## Recommended unified interface

Add one **Research Evidence** tab beside the current Dictionary and Predictor tabs:

1. User selects a grass in the existing dictionary.
2. The current project displays its measured values and Phase 2 predictions as it already does.
3. Research Evidence loads the same species from this SQLite graph.
4. It shows related mechanisms/genes, supporting source text, source paper link and review status.
5. A separate **Research opportunities** view ranks graph coverage gaps with a visible explanation and next validation action.

## Recommended supervisor wording

> Our system has four connected layers. The first is a structured grass data library. The second is a regression-based predictor with separate individual-species and mechanism-group modes. The third is the dashboard for exploring values and model metrics. The fourth is an evidence-grounded knowledge graph that links grasses to published salt-tolerance mechanisms, genes and applications. Every literature edge keeps its source paper and supporting text, while model predictions remain labelled as predictions. This makes the project useful both as a data tool and as a research-discovery prototype.

## Scale-up plan

| Stage | Corpus size | What changes | Quality gate |
|---|---:|---|---|
| Demonstration | 2–20 papers | Included seed records plus a small manual review set | All shown evidence manually checked |
| Pilot | 100–300 abstracts | Run PubMed collector and LLM extraction; normalise repeated species names | Random audit of 100 extracted edges; report precision and rejection rate |
| Project-scale | 1,000–5,000 abstracts | Batch collection, cache raw XML, use an API key, queue review by confidence | Duplicate rate, schema validity, evidence-quote pass rate and sampled precision recorded |
| Future research-scale | 10,000+ papers / open full text | Migrate the same node/edge schema to Neo4j and add embeddings | Formal protocol, inter-annotator checks and source-license review |

## What may be claimed responsibly

The project may say it is a **prototype literature knowledge graph** and that it surfaces **research leads based on graph coverage**. It should not claim that a low-degree species is truly understudied, that a link is novel, or that a gene will improve a crop without manual literature verification and experimental validation.
