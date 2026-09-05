# Model Context Protocol (MCP) Tool Subsystem

## Overview
The chatbot incorporates a standard Model Context Protocol (MCP) server built with official Python SDK v2 (`mcp>=2.0.0`).

## Tool Scope
1. **`lookup_medical_term`**: Accepts a medical abbreviation, acronym, or clinical term and returns its standardized definition and reference classification.
2. **Deterministic & Testable**: Operates entirely offline from curated terminology data, preventing hallucinated acronym definitions.
