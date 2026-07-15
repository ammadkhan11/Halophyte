# Halophyte Research Knowledge Graph

Phase 4 of the Halophyte project: a literature-evidence layer that connects the existing grass dictionary and salt/ion prediction work to scientific papers, mechanisms, genes, habitats, applications and research opportunities.

It is deliberately built as a **reproducible local SQLite graph** for the final-year-project demo. It needs no database server and can later be moved to Neo4j without changing the extraction schema. Every literature relationship retains a source paper, a supporting evidence span and a confidence score; the interface never presents an LLM claim without its provenance.

## What this module delivers

- PubMed corpus collection with rate-safe local caching.
- Strict JSON schema for LLM extraction, including an exact supporting text span for every claim.
- SQLite graph with `Species`, `Gene`, `Mechanism`, `SalinityThreshold`, `Geography`, `Application` and `Paper` nodes.
- Species-name normalisation and duplicate protection.
- A Streamlit research dashboard: search, inspect cited evidence, browse the graph and view ranked research opportunities.
- A Phase 1 importer that turns the grass dictionary's species, mechanism and GR50 columns into provenance-labelled graph facts.
- A transparent gap-analysis report; its output is a prioritised **research lead**, not a proven biological conclusion.

## Quick start

```bash
cd halophyte_knowledge_graph
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt

python -m src.cli seed
streamlit run src/app.py
```

The included demonstration records are small, clearly labelled and source-linked. For a project presentation, use them to show the full workflow first; then collect a real corpus and run extraction before claiming larger-scale findings.

## Daily working flow

```bash
# 1. Collect papers from PubMed (respect NCBI's usage policy and provide your email)
python -m src.cli collect --query 'halophyte salt tolerance' --retmax 100 --email your.email@example.com

# 2. Extract with an OpenAI-compatible LLM. It rejects ungrounded relationships.
export OPENAI_API_KEY='...'
python -m src.cli extract --limit 100

# 3. Review queued claims in the dashboard, approve only evidence-supported ones,
#    then generate a transparent research-opportunity report.
python -m src.cli report
```

`extract` expects the official OpenAI Python package and `OPENAI_API_KEY`; replace the small client in `src/extraction.py` if your institution uses a different model provider. A model is an assistant to extraction—not a source of truth. It is required to return an exact evidence quote already contained in the stored abstract, otherwise that claim is rejected.

## Adding your existing Phase 1 data

Export the current dictionary master table as a CSV and run:

```bash
python -m src.cli import-phase1 --csv /path/to/halophyte_master.csv
```

Recognised column alternatives include `species`, `grass species`, `common name`, `mechanism`, `gr50_avg`, `gr50_mid`, and `gr50 (ds/m)`. Imported rows are linked to the `Dataset: Phase 1 Grass Dictionary` provenance record. The current Phase 2 individual-grass and mechanism-based predictors remain separate prediction models; this graph gives them an evidence/explanation layer rather than replacing their calculated values.

## Project boundary and methodology

The demo graph is not a systematic review and it does not make biomedical or agronomic recommendations. Quantitative tolerance values remain unit-labelled and source-specific. Before submitting graph-wide results, manually audit at least 100 sampled relationships and report precision, rejection rate and coverage as described in `docs/METHODOLOGY.md`.

See `docs/PROJECT_INTEGRATION.md` for how this is presented as Phase 4 of the full project and `docs/DEMO_SCRIPT.md` for a concise supervisor demonstration.
