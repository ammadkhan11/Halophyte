"""Shared, conservative schema for evidence-grounded literature extraction."""

from __future__ import annotations

ENTITY_TYPES = {
    "Species",
    "Gene",
    "Mechanism",
    "SalinityThreshold",
    "Geography",
    "Application",
}

RELATION_TYPES = {
    "HAS_MECHANISM",
    "EXPRESSES_GENE",
    "FOUND_IN",
    "USED_FOR",
    "TOLERATES_UP_TO",
    "STUDIED_IN",
}

EXTRACTION_JSON_SCHEMA = {
    "name": "halophyte_literature_extraction",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": sorted(ENTITY_TYPES)},
                        "canonical_name": {"type": "string"},
                    },
                    "required": ["name", "type", "canonical_name"],
                },
            },
            "relations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                        "type": {"type": "string", "enum": sorted(RELATION_TYPES)},
                        "value": {"type": ["number", "null"]},
                        "unit": {"type": ["string", "null"]},
                        "evidence_quote": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["source", "target", "type", "value", "unit", "evidence_quote", "confidence"],
                },
            },
        },
        "required": ["entities", "relations"],
    },
}

SYSTEM_PROMPT = """You are extracting only explicit, evidence-grounded claims from a scientific abstract about halophytes and salt tolerance. Return JSON that follows the provided schema. Do not infer missing biology. For every relationship, evidence_quote must be an exact contiguous quote from the abstract (at least 12 characters), and source and target must match an extracted entity name or canonical_name. Only report a numeric salinity threshold when a number and unit are stated in the abstract. Use confidence below 0.70 for ambiguous language."""
