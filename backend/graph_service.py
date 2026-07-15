from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GRAPH_ROOT = PROJECT_ROOT / "halophyte_knowledge_graph"
PHASE1_CSV_PATH = PROJECT_ROOT / "ml" / "data" / "halophyte_grass_library.csv"

if str(GRAPH_ROOT) not in sys.path:
    sys.path.insert(0, str(GRAPH_ROOT))

from src.analysis import research_opportunities  # noqa: E402
from src.graph_store import GraphStore  # noqa: E402
from src.schema import ENTITY_TYPES  # noqa: E402

VISIBLE_EVIDENCE_STATUSES = {"approved", "demo_reviewed", "dataset_import"}


def _with_store(callback):
    store = GraphStore()
    try:
        return callback(store)
    finally:
        store.close()


def ensure_graph_initialized() -> dict[str, int]:
    def initialize(store: GraphStore) -> dict[str, int]:
        counts = store.dashboard_counts()
        if counts["nodes"] == 0 and counts["edges"] == 0:
            store.seed_demo()
            counts = store.dashboard_counts()
        return counts

    return _with_store(initialize)


def _row_to_node(row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "node_type": row["node_type"],
        "display_name": row["display_name"],
        "canonical_name": row["canonical_name"],
        "attributes": json.loads(row["attributes_json"] or "{}"),
    }


def _row_to_edge(row) -> dict[str, Any]:
    paper_url = row["paper_url"] if "paper_url" in row.keys() else None
    paper_title = row["paper_title"] if "paper_title" in row.keys() else None
    paper_external_id = row["paper_external_id"] if "paper_external_id" in row.keys() else None
    return {
        "id": int(row["id"]),
        "source_id": int(row["source_id"]),
        "source_name": row["source_name"],
        "source_type": row["source_type"] if "source_type" in row.keys() else None,
        "target_id": int(row["target_id"]),
        "target_name": row["target_name"],
        "target_type": row["target_type"] if "target_type" in row.keys() else None,
        "relation_type": row["relation_type"],
        "numeric_value": row["numeric_value"],
        "unit": row["unit"],
        "evidence_quote": row["evidence_quote"],
        "confidence": float(row["confidence"]),
        "review_status": row["review_status"],
        "paper_external_id": paper_external_id,
        "paper_title": paper_title,
        "paper_url": paper_url,
        "has_literature_provenance": bool(paper_external_id),
    }


def graph_overview() -> dict[str, int]:
    return _with_store(lambda store: store.dashboard_counts())


def seed_demo_graph() -> dict[str, int]:
    def seed(store: GraphStore) -> dict[str, int]:
        store.seed_demo()
        return store.dashboard_counts()

    return _with_store(seed)


def import_phase1_csv(csv_path: str | None = None) -> dict[str, int]:
    path = Path(csv_path) if csv_path else PHASE1_CSV_PATH
    if not path.exists():
        raise FileNotFoundError(f"Phase 1 CSV not found: {path}")
    return _with_store(lambda store: store.import_phase1_csv(path))


def search_entities(query: str = "", node_type: str | None = None) -> dict[str, Any]:
    if node_type and node_type != "All" and node_type not in ENTITY_TYPES:
        raise ValueError(f"Unknown entity type: {node_type}")

    def search(store: GraphStore) -> dict[str, Any]:
        return {
            "entity_types": sorted(ENTITY_TYPES),
            "entities": [_row_to_node(row) for row in store.search(query, node_type)],
        }

    return _with_store(search)


def entity_details(node_id: int) -> dict[str, Any]:
    def details(store: GraphStore) -> dict[str, Any]:
        node, edges = store.node_details(node_id)
        if not node:
            raise LookupError(f"Entity not found: {node_id}")
        return {
            "entity": _row_to_node(node),
            "evidence": [_row_to_edge(row) for row in edges],
        }

    return _with_store(details)


def _matches_filter(edge: dict[str, Any], node_type: str, value: str) -> bool:
    needle = value.strip().casefold()
    if not needle:
        return True
    source_matches = edge.get("source_type") == node_type and needle in edge["source_name"].casefold()
    target_matches = edge.get("target_type") == node_type and needle in edge["target_name"].casefold()
    return source_matches or target_matches


def graph_evidence(
    species: str = "",
    mechanism: str = "",
    gene: str = "",
    application: str = "",
    geography: str = "",
    status: str | None = None,
) -> list[dict[str, Any]]:
    def evidence(store: GraphStore) -> list[dict[str, Any]]:
        rows = [_row_to_edge(row) for row in store.graph_edges(status if status and status != "All" else None)]
        filters = [
            ("Species", species),
            ("Mechanism", mechanism),
            ("Gene", gene),
            ("Application", application),
            ("Geography", geography),
        ]
        for node_type, value in filters:
            if value.strip():
                rows = [edge for edge in rows if _matches_filter(edge, node_type, value)]
        return rows

    return _with_store(evidence)


def graph_edges(status: str | None = None) -> list[dict[str, Any]]:
    return _with_store(lambda store: [_row_to_edge(row) for row in store.graph_edges(status if status != "All" else None)])


def opportunities() -> list[dict[str, Any]]:
    return _with_store(research_opportunities)


def update_review_status(edge_id: int, status: str) -> dict[str, Any]:
    if status not in {"approved", "rejected", "pending", "needs_source_review"}:
        raise ValueError("Review status must be approved, rejected, pending, or needs_source_review.")

    def update(store: GraphStore) -> dict[str, Any]:
        store.set_review_status(edge_id, status)
        updated = [edge for edge in store.graph_edges() if int(edge["id"]) == edge_id]
        if not updated:
            raise LookupError(f"Evidence relationship not found: {edge_id}")
        return _row_to_edge(updated[0])

    return _with_store(update)
