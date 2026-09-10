"""
Tests for the MCP Healthcare Reference Server (backend/app/mcp/server.py).

Covers:
- Tool registration and schema
- Valid terminology lookups (exact, fuzzy, case-insensitive)
- Unknown term lookups
- Input validation (empty, whitespace-only, overly long, invalid types)
"""

import pytest
from app.mcp.server import server, lookup_medical_term


@pytest.mark.asyncio
async def test_mcp_server_tool_registered():
    """Verify lookup_medical_term is properly registered as an MCP tool."""
    tools = await server.list_tools()
    tool_names = [tool.name for tool in tools]
    assert "lookup_medical_term" in tool_names


def test_mcp_lookup_known_term_exact():
    """Exact match lookup returns complete structured data."""
    result = lookup_medical_term("hypertension")
    assert result["status"] == "found"
    assert result["term"] == "hypertension"
    assert result["normalized_term"] == "hypertension"
    assert "Hypertension" in result["canonical_name"]
    assert "blood pressure" in result["definition"].lower()
    assert result["category"] == "Cardiovascular"
    assert "AHA" in result["clinical_reference"] or "CDC" in result["clinical_reference"]
    assert isinstance(result["related_terms"], list)
    assert len(result["related_terms"]) > 0


def test_mcp_lookup_case_insensitive_and_whitespace():
    """Casing and surrounding/internal whitespace should normalize cleanly."""
    result = lookup_medical_term("   Systolic   Blood   Pressure   ")
    assert result["status"] == "found"
    assert result["normalized_term"] == "systolic blood pressure"
    assert "Systolic" in result["canonical_name"]


def test_mcp_lookup_alias_dash_diet():
    """Look up DASH diet concept."""
    result = lookup_medical_term("DASH diet")
    assert result["status"] == "found"
    assert "DASH" in result["canonical_name"]
    assert "sodium" in result["definition"].lower()


def test_mcp_lookup_unknown_term():
    """Unrecognized medical term returns not_found status with safe message."""
    result = lookup_medical_term("xenomorphic_syndrome_xyz")
    assert result["status"] == "not_found"
    assert result["canonical_name"] is None
    assert result["definition"] is None
    assert "not found" in result["message"].lower()


def test_mcp_lookup_empty_input():
    """Empty or whitespace-only input triggers validation error."""
    res1 = lookup_medical_term("")
    assert res1["status"] == "error"
    assert "empty" in res1["message"].lower()

    res2 = lookup_medical_term("     ")
    assert res2["status"] == "error"
    assert "empty" in res2["message"].lower()


def test_mcp_lookup_overly_long_input():
    """Inputs exceeding 100 characters are rejected with validation error."""
    long_term = "a" * 105
    result = lookup_medical_term(long_term)
    assert result["status"] == "error"
    assert "exceeds" in result["message"].lower() or "100" in result["message"]


def test_mcp_lookup_invalid_type():
    """Non-string inputs return validation error."""
    result = lookup_medical_term(12345)  # type: ignore
    assert result["status"] == "error"
    assert "string" in result["message"].lower()
