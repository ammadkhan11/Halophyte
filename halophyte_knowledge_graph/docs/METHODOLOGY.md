# Methodology and Quality Assurance

## 1. Corpus acquisition

The collector queries PubMed through the NCBI E-utilities API. For each record it stores the PubMed identifier, title, authors, journal, year, DOI where provided, canonical PubMed URL and abstract. The raw XML response is cached locally so that parsing and extraction are reproducible without another network call.

Initial query families should include:

- `halophyte AND salt tolerance`
- `salinity stress AND plant AND ion compartmentalization`
- named project species plus `salinity`
- `SOS1 OR NHX1 OR HKT1` combined with `halophyte`
- `biosaline agriculture AND halophyte`

Use abstracts as the baseline corpus. Add open-access full text only where the licence allows it and preserve the exact source section used for extraction.

## 2. Extraction schema

Entities are `Species`, `Gene`, `Mechanism`, `SalinityThreshold`, `Geography` and `Application`. Relationships include `HAS_MECHANISM`, `EXPRESSES_GENE`, `FOUND_IN`, `USED_FOR`, `TOLERATES_UP_TO` and `STUDIED_IN`.

Each relationship stores five non-negotiable provenance fields:

1. Source paper identifier and link.
2. Exact supporting quote present in stored source text.
3. Extraction confidence.
4. Review status.
5. Timestamp.

The ingestion code rejects a relationship when its quoted evidence does not occur verbatim in the paper abstract, or when either endpoint was not extracted as a typed entity.

## 3. Normalisation

Entities are case-folded and whitespace-normalised, and aliases are stored separately from the display name. At a larger scale, species should be resolved against the GBIF taxonomic backbone and genes against UniProt or NCBI Gene. Do not merge names automatically when the resolver is uncertain; add the relationship to the review queue instead.

## 4. Review protocol

For every new extraction batch, randomly sample at least 100 candidate edges. A reviewer checks: (a) the source and target are correctly typed; (b) the relation is explicitly supported; (c) the quote is relevant; and (d) units and values are copied correctly.

Report:

\[
Precision = \frac{\text{correct sampled edges}}{\text{sampled edges}}, \qquad
Quote\ pass\ rate = \frac{\text{edges with verbatim evidence}}{\text{candidate edges}}
\]

Also report rejected edges, unresolved entities, duplicate aliases and the number of abstracts without extractable claims. This is much stronger academically than reporting only the total number of graph edges.

## 5. Research-opportunity analysis

The module produces three cautious graph-structure signals:

- **Underconnected species:** currently few verified relationships in the collected graph.
- **Comparative-study leads:** species sharing a recorded mechanism but not yet linked by a known comparison in the current corpus.
- **Sparse translation areas:** mechanisms frequent in halophyte evidence but with weak application/crop connections.

These are ranked evidence-coverage signals. Before presenting any one as a novel hypothesis, the linked papers must be reviewed and a targeted literature search performed.
