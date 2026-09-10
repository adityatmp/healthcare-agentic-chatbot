# Model Context Protocol (MCP) Integration

## 1. Overview & Motivation

In enterprise and clinical AI architectures, applications must interface with external tools, authoritative datasets, and domain-specific services without hardcoding monolithic helper functions directly into the prompt pipeline. 

The **Model Context Protocol (MCP)** is an open protocol developed to standardize how AI applications discover, inspect, and invoke tools, resources, and prompts over well-defined boundaries.

### Why MCP in this Project?
- **Protocol Boundary**: Instead of burying a private Python function inside the agent code, the clinical terminology lookup capability is exposed as an MCP tool via an official MCP server (`MCPServer`).
- **Standardized Schema & Discovery**: The MCP client dynamically negotiates capabilities, performs tool discovery (`tools/list`), and executes tools (`tools/call`) using structured JSON-RPC protocol messages.
- **Interoperability**: The `MCPServer` can be executed standalone over standard `stdio` or embedded within an application bridge, making the healthcare reference service accessible to other MCP-compliant hosts (e.g. IDEs, external agent runtimes) without modifying backend business logic.
- **Auditability & Governance**: Tool calls are distinct protocol events with latency, input schemas, and explicit execution boundaries, enabling strict logging and compliance tracking.

---

## 2. MCP Architecture & Component Separation

The runtime architecture separates concerns across five distinct layers:

```
FastAPI Backend (/chat)
         │
         ▼
    ChatService
         │
         ▼
    AgentRouter (Intent Classifier: Route.MCP)
         │
         ▼
 MCPTerminologyClient (mcp.client.Client bridge)
         │
         ▼  [JSON-RPC Protocol: initialize -> tools/list -> tools/call]
     MCPServer ("healthcare-reference-server")
         │
         ▼
Tool: "lookup_medical_term"
         │
         ▼
Authoritative Clinical Dataset (CDC / AHA / WHO)
```

1. **MCPServer (`backend/app/mcp/server.py`)**:
   - Built on official `mcp>=2.0.0` (`mcp.server.mcpserver.MCPServer`).
   - Registers `@server.tool(name="lookup_medical_term")`.
   - Supports standalone stdio execution (`python -m app.mcp.server`).
2. **Clinical Dataset (`backend/app/mcp/dataset.py`)**:
   - Curated reference glossary containing standard clinical definitions, categories, authoritative references, and related terms (e.g., `hypertension`, `systolic blood pressure`, `diastolic blood pressure`, `dash diet`, `tachycardia`, `bradycardia`, `hypotension`, `arrhythmia`, `atherosclerosis`, `myocardial infarction`).
3. **MCPTerminologyClient Bridge (`backend/app/mcp/client.py`)**:
   - Uses `mcp.client.Client` to establish protocol sessions.
   - Manages asynchronous tool discovery and invocation.
   - Provides safe synchronous execution wrapper (`lookup_term_sync`) for non-blocking integration with synchronous request handlers.
4. **Agent Router (`backend/app/agents/router.py`)**:
   - Evaluates intent: routes terminology definition queries to `Route.MCP` while preserving strict precedence for `Route.SAFETY`.
   - Formats structured tool results into grounded, authoritative responses with `tool_used="lookup_medical_term"`.

---

## 3. Tool Specification & Schema

### Tool: `lookup_medical_term`

- **Name**: `lookup_medical_term`
- **Description**: Look up authoritative clinical definitions, medical classifications, and guidance for standard healthcare and clinical terms.
- **Transport**: In-process protocol session or Stdio subprocess (`mcp.client.stdio.StdioServerParameters`).

#### Input Schema
| Parameter | Type | Required | Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `term` | `string` | Yes | 1–100 chars, non-empty | The clinical concept or medical term to look up. |

#### Output Schema
```json
{
  "term": "string",
  "normalized_term": "string",
  "canonical_name": "string | null",
  "definition": "string | null",
  "category": "string | null",
  "clinical_reference": "string | null",
  "related_terms": ["string"],
  "status": "found | not_found | error",
  "message": "string (optional)"
}
```

---

## 4. Agent Routing & Safety-First Precedence

The agent router evaluates incoming queries with a strict hierarchical pipeline:

1. **Safety Guardrails (First Priority)**:
   - Acute medical emergencies (chest pain, breathing difficulty, severe bleeding, stroke, anaphylaxis).
   - Clinical action requests (personal diagnosis, prescription, medication changes).
   - **Crucial Rule**: Terminology words present in a safety-critical query NEVER bypass safety. For example, `"I have chest pain, what is the definition?"` is routed to `Route.SAFETY`, not `Route.MCP`.
2. **MCP Terminology Routing (Second Priority)**:
   - Matches definition and terminology intent patterns (e.g. `"What does X mean?"`, `"Define X"`, `"What is X?"`, `"Meaning of X"`).
   - Extracts and sanitizes the target term.
   - Excludes procedural or clinical guidance queries (e.g. queries containing `"treatment"`, `"lifestyle modifications"`, `"how to"`) to ensure they route to RAG.
3. **Grounded RAG (Third Priority)**:
   - General healthcare knowledge queries are retrieved from the vector database against ingested medical literature.

---

## 5. Security & Input Sanitization

- **Untrusted User Input**: All parameters supplied to `lookup_medical_term` are treated as untrusted user input.
- **Length & Type Validation**: Strict validation rejects non-string inputs, empty strings, and inputs exceeding 100 characters.
- **Normalization**: Input strings are stripped of punctuation and control characters, eliminating injection vectors.
- **Zero Filesystem / Command Execution**: The tool performs lookups strictly against a verified in-memory dictionary; no arbitrary shell commands or unvalidated filesystem reads are permitted.

---

## 6. Failure Handling & Observability

- **Tool Unavailable / Timeout**: If the MCP server fails to respond within the configured timeout (`10.0s`), the client traps the exception and returns a graceful error dictionary (`status="error"`).
- **Term Not Found**: When a concept is absent from the glossary, the tool returns `status="not_found"`. The router translates this into a clean, safe abstention informing the user that the term is not in the glossary.
- **Zero Stack Trace Leakage**: Raw exceptions (`MCPError`, `TimeoutError`) are logged internally with request tracking IDs but never exposed to the frontend or user.
- **Observability**: Every invocation logs tool name, execution latency in milliseconds, and success/failure status.

---

## 7. Current Limitations

- **Curated Static Glossary**: The terminology dataset currently covers major cardiovascular, hemodynamic, and vital signs concepts. Unlisted rare conditions return a safe `not_found` response.
- **Single-Tool Scope**: Milestone 5 implements one dedicated reference tool (`lookup_medical_term`). Multi-tool chaining or dynamic tool selection across multiple external servers can be extended in future milestones.
