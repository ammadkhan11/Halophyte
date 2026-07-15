"""Evidence-first LLM extraction and conservative graph ingestion."""

from __future__ import annotations

import json
import os
from typing import Any

from .graph_store import GraphStore
from .schema import ENTITY_TYPES, EXTRACTION_JSON_SCHEMA, RELATION_TYPES, SYSTEM_PROMPT


def extract_with_openai(title: str, abstract: str, model: str = "gpt-4.1-mini") -> dict[str, Any]:
    """Request schema-constrained extraction. Called only when an API key exists."""
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_schema", "json_schema": {"name": EXTRACTION_JSON_SCHEMA["name"], "strict": True, "schema": EXTRACTION_JSON_SCHEMA["schema"]}},
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": f"TITLE: {title}\n\nABSTRACT:\n{abstract}"}],
        temperature=0,
    )
    return json.loads(response.choices[0].message.content or "{}")


def validate_and_ingest(store: GraphStore, paper_external_id: str, extraction: dict[str, Any]) -> dict[str, int]:
    """Reject relations that are not literally grounded in the stored abstract."""
    paper = store.conn.execute("SELECT * FROM papers WHERE external_id=?", (paper_external_id,)).fetchone()
    if not paper:
        raise ValueError(f"Unknown paper {paper_external_id}")
    canonical: dict[str, tuple[str, str]] = {}
    result = {"nodes": 0, "accepted": 0, "rejected": 0}
    for item in extraction.get("entities", []):
        node_type, name = item.get("type"), item.get("canonical_name") or item.get("name")
        if node_type not in ENTITY_TYPES or not isinstance(name, str) or not name.strip():
            result["rejected"] += 1
            continue
        store.upsert_node(node_type, name, [item.get("name", "")])
        canonical[item.get("name", "").casefold()] = (node_type, name)
        canonical[name.casefold()] = (node_type, name)
        result["nodes"] += 1
    abstract = (paper["abstract"] or "").casefold()
    for relation in extraction.get("relations", []):
        quote = relation.get("evidence_quote", "").strip()
        source_key, target_key = str(relation.get("source", "")).casefold(), str(relation.get("target", "")).casefold()
        if (relation.get("type") not in RELATION_TYPES or not quote or quote.casefold() not in abstract
                or source_key not in canonical or target_key not in canonical):
            result["rejected"] += 1
            continue
        source_name, target_name = canonical[source_key][1], canonical[target_key][1]
        confidence = float(relation.get("confidence", 0))
        status = "pending" if confidence >= 0.70 else "needs_source_review"
        store.add_edge(source_name, target_name, relation["type"], paper_external_id, quote, confidence, status,
                       relation.get("value"), relation.get("unit"))
        result["accepted"] += 1
    return result


def extract_unprocessed(store: GraphStore, limit: int, model: str) -> dict[str, int]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. No extraction was attempted.")
    total = {"papers": 0, "nodes": 0, "accepted": 0, "rejected": 0}
    for paper in store.papers_without_extraction(limit):
        if not paper["abstract"]:
            continue
        result = validate_and_ingest(store, paper["external_id"], extract_with_openai(paper["title"], paper["abstract"], model))
        total["papers"] += 1
        for key in ("nodes", "accepted", "rejected"):
            total[key] += result[key]
    return total
