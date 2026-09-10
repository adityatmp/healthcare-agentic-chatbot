"""
Model Context Protocol (MCP) Healthcare Reference Server.

Exposes authoritative clinical terminology lookup tools compliant with the
official MCP 2.x specification (mcp.server.mcpserver.MCPServer).
"""

import logging
import re
from typing import Any

from mcp.server.mcpserver import MCPServer
from app.mcp.dataset import CLINICAL_TERMINOLOGY

logger = logging.getLogger("healthcare_chatbot.mcp.server")

# Initialize MCP Server instance
server = MCPServer(
    name="healthcare-reference-server",
    instructions="Authoritative healthcare reference server providing deterministic clinical terminology definitions.",
)


def _normalize_lookup_key(term: str) -> str:
    """Normalize input term for fuzzy key matching against the clinical glossary."""
    cleaned = re.sub(r"[^\w\s-]", "", term.lower())
    return " ".join(cleaned.split())


@server.tool(
    name="lookup_medical_term",
    description=(
        "Look up authoritative clinical definitions, medical classifications, "
        "and guidance for standard healthcare and clinical terms."
    ),
)
def lookup_medical_term(term: str) -> dict[str, Any]:
    """Look up a medical term in the authoritative clinical glossary.

    Args:
        term: Medical or clinical concept to look up (1-100 characters).

    Returns:
        Structured dictionary containing definition, category, references, and status.
    """
    if not isinstance(term, str):
        return {
            "term": str(term),
            "normalized_term": "",
            "canonical_name": None,
            "definition": None,
            "category": None,
            "clinical_reference": None,
            "related_terms": [],
            "status": "error",
            "message": "Input 'term' must be a valid string.",
        }

    trimmed = term.strip()

    if not trimmed:
        return {
            "term": term,
            "normalized_term": "",
            "canonical_name": None,
            "definition": None,
            "category": None,
            "clinical_reference": None,
            "related_terms": [],
            "status": "error",
            "message": "Term must not be empty or whitespace-only.",
        }

    if len(trimmed) > 100:
        return {
            "term": trimmed[:100] + "...",
            "normalized_term": "",
            "canonical_name": None,
            "definition": None,
            "category": None,
            "clinical_reference": None,
            "related_terms": [],
            "status": "error",
            "message": "Term exceeds maximum allowable length of 100 characters.",
        }

    norm_key = _normalize_lookup_key(trimmed)
    logger.info("MCP lookup_medical_term invoked for '%s' (normalized: '%s')", trimmed, norm_key)

    # 1. Exact match
    if norm_key in CLINICAL_TERMINOLOGY:
        entry = CLINICAL_TERMINOLOGY[norm_key]
        return {
            "term": trimmed,
            "normalized_term": norm_key,
            "canonical_name": entry["canonical_name"],
            "definition": entry["definition"],
            "category": entry["category"],
            "clinical_reference": entry["clinical_reference"],
            "related_terms": entry.get("related_terms", []),
            "status": "found",
        }

    # 2. Substring / alias search
    for key, entry in CLINICAL_TERMINOLOGY.items():
        if norm_key == key or norm_key in key or key in norm_key:
            return {
                "term": trimmed,
                "normalized_term": key,
                "canonical_name": entry["canonical_name"],
                "definition": entry["definition"],
                "category": entry["category"],
                "clinical_reference": entry["clinical_reference"],
                "related_terms": entry.get("related_terms", []),
                "status": "found",
            }

    logger.info("Term '%s' not found in clinical reference dataset", trimmed)
    return {
        "term": trimmed,
        "normalized_term": norm_key,
        "canonical_name": None,
        "definition": None,
        "category": None,
        "clinical_reference": None,
        "related_terms": [],
        "status": "not_found",
        "message": f"Term '{trimmed}' was not found in the authoritative healthcare reference glossary.",
    }


if __name__ == "__main__":
    server.run(transport="stdio")
