"""Transparent, non-speculative research opportunity ranking."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .graph_store import GraphStore, ROOT


def research_opportunities(store: GraphStore) -> list[dict]:
    """Rank visible graph gaps. Scores describe evidence coverage, not biological likelihood."""
    edges = [e for e in store.graph_edges() if e["review_status"] in {"approved", "demo_reviewed", "dataset_import"}]
    nodes = store.search()
    degree: dict[int, int] = defaultdict(int)
    species_mechanisms: dict[str, set[str]] = defaultdict(set)
    mechanism_species: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        degree[edge["source_id"]] += 1
        degree[edge["target_id"]] += 1
        if edge["relation_type"] == "HAS_MECHANISM" and edge["source_type"] == "Species":
            species_mechanisms[edge["source_name"]].add(edge["target_name"])
            mechanism_species[edge["target_name"]].add(edge["source_name"])
    opportunities: list[dict] = []
    for node in nodes:
        if node["node_type"] == "Species" and degree[node["id"]] <= 1:
            opportunities.append({"kind": "Underconnected species", "subject": node["display_name"], "score": 100 - 20 * degree[node["id"]],
                                  "reason": f"Only {degree[node['id']]} verified graph relationship(s) are currently recorded.",
                                  "next_step": "Prioritise literature collection and manual extraction before concluding that the species is understudied."})
    species = sorted(species_mechanisms)
    for i, first in enumerate(species):
        for second in species[i + 1:]:
            shared = species_mechanisms[first] & species_mechanisms[second]
            if shared:
                opportunities.append({"kind": "Comparative-study lead", "subject": f"{first} ↔ {second}", "score": 50 + 10 * len(shared),
                                      "reason": f"They share recorded mechanism(s): {', '.join(sorted(shared))}.",
                                      "next_step": "Check whether the linked papers already compare this pair; if not, consider a controlled comparative study."})
    return sorted(opportunities, key=lambda item: (-item["score"], item["subject"]))


def write_report(store: GraphStore, output: str | Path | None = None) -> Path:
    path = Path(output or ROOT / "data" / "opportunities.json")
    path.write_text(json.dumps({"generated_from": "visible approved/demo/dataset edges", "opportunities": research_opportunities(store)}, indent=2), encoding="utf-8")
    return path
