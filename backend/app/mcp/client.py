"""
Model Context Protocol (MCP) Client Bridge.

Provides client-side session management, tool discovery, structured invocation,
and safe exception handling for the healthcare reference MCP server.
"""

import asyncio
import json
import logging
import threading
import time
from typing import Any

from mcp.client import Client
from mcp.server.mcpserver import MCPServer
from app.mcp.server import server as default_server

logger = logging.getLogger("healthcare_chatbot.mcp.client")


class MCPClientError(Exception):
    """Base exception for MCP client bridge errors."""

    pass


class MCPTerminologyClient:
    """Client bridge for invoking tools on the healthcare MCP server."""

    def __init__(self, target_server: MCPServer | None = None, timeout_sec: float = 10.0):
        self.target_server = target_server or default_server
        self.timeout_sec = timeout_sec

    async def lookup_term(self, term: str) -> dict[str, Any]:
        """Look up a clinical term by invoking the MCP tool over the protocol.

        Args:
            term: Medical term to query.

        Returns:
            Structured dictionary with term details or safe failure message.
        """
        start_time = time.time()
        tool_name = "lookup_medical_term"
        logger.info("MCP Client: Requesting tool '%s' with term='%s'", tool_name, term)

        try:
            async with Client(self.target_server) as client:
                # 1. Discover tools across protocol boundary
                tools_result = await client.list_tools()
                available_tools = [t.name for t in tools_result.tools]

                if tool_name not in available_tools:
                    logger.error("MCP tool '%s' not registered on target server", tool_name)
                    return {
                        "term": term,
                        "status": "error",
                        "message": f"MCP tool '{tool_name}' is not registered on the server.",
                    }

                # 2. Invoke tool with parameters
                call_result = await client.call_tool(
                    name=tool_name,
                    arguments={"term": term},
                )

                latency_ms = round((time.time() - start_time) * 1000, 2)
                logger.info(
                    "MCP Client: Received response from '%s' in %sms (is_error=%s)",
                    tool_name,
                    latency_ms,
                    call_result.is_error,
                )

                if call_result.is_error:
                    error_text = (
                        call_result.content[0].text
                        if call_result.content
                        else "Unknown MCP tool error"
                    )
                    logger.warning("MCP tool reported execution error: %s", error_text)
                    return {
                        "term": term,
                        "status": "error",
                        "message": "Clinical reference tool reported an execution error.",
                    }

                # 3. Parse structured JSON from protocol response content
                if not call_result.content:
                    return {
                        "term": term,
                        "status": "error",
                        "message": "Clinical reference tool returned empty content.",
                    }

                raw_text = call_result.content[0].text
                try:
                    data = json.loads(raw_text)
                    return data
                except (json.JSONDecodeError, TypeError):
                    return {
                        "term": term,
                        "status": "error",
                        "message": "Malformed response payload from clinical reference tool.",
                    }

        except Exception as exc:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "MCP Client invocation failed for '%s' after %sms: %s",
                tool_name,
                latency_ms,
                str(exc),
            )
            return {
                "term": term,
                "status": "error",
                "message": "The clinical reference tool is temporarily unavailable.",
            }

    def lookup_term_sync(self, term: str) -> dict[str, Any]:
        """Synchronous wrapper for lookup_term to support synchronous agent pipelines."""
        result: dict[str, Any] = {}
        exception: Exception | None = None

        def _worker():
            nonlocal result, exception
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    asyncio.wait_for(self.lookup_term(term), timeout=self.timeout_sec)
                )
            except Exception as e:
                exception = e
            finally:
                loop.close()

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout_sec + 2.0)

        if thread.is_alive():
            logger.error("MCP synchronous call timed out after %s seconds", self.timeout_sec)
            return {
                "term": term,
                "status": "error",
                "message": "The clinical reference tool timed out.",
            }

        if exception:
            logger.error("MCP synchronous execution encountered exception: %s", str(exception))
            return {
                "term": term,
                "status": "error",
                "message": "The clinical reference tool encountered an execution error.",
            }

        return result
