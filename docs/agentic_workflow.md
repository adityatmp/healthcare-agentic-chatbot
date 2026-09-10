# Agentic Workflow & Orchestration Architecture

## 1. Architectural Overview & Motivation

In a high-stakes domain like healthcare, feeding every user query directly into a generic Retrieval-Augmented Generation (RAG) pipeline is unsafe and inefficient. An orchestration layer acts as an explicit decision boundary that inspects incoming user queries before initiating vector retrieval, tool invocation, or LLM inference.

### Why an Orchestration Layer Exists
- **Safety Gatekeeping**: Critical medical emergencies, direct diagnosis requests, and medication alteration inquiries must never be handled by open-ended text generation.
- **Dynamic Capability Selection**: Medical terminology definitions are handled via an authoritative Model Context Protocol (MCP) tool, while broad clinical questions route to grounded RAG.
- **Resource Efficiency**: Bypassing embedding generation and vector database queries for queries that cannot safely be answered or are handled by reference tools saves computational overhead.
- **Deterministic Predictability**: Safety guardrails in healthcare must behave transparently and predictably rather than relying on non-deterministic model self-policing.

---

## 2. Decision Flow & Architecture Diagram

```
                                  User Request
                                       │
                                       ▼
                                FastAPI /chat
                                       │
                                       ▼
                                  ChatService
                                       │
                                       ▼
                                  AgentRouter
                         (Normalized Pattern Matching)
                                       │
      ┌────────────────────────────────┼────────────────────────────────┐
      ▼                                ▼                                ▼
[Route.SAFETY]                   [Route.MCP]                      [Route.RAG]
Emergencies & Diagnoses       Medical Terminology Queries     General Healthcare Knowledge
      │                                │                                │
      ▼                                ▼                                ▼
Conservative Refusal          MCPTerminologyClient              RAG Engine Retrieval
- Grounded: False             (mcp.client.Client bridge)        (Embedding + ChromaDB)
- Abstained: True                      │                                │
- Zero Vector/LLM compute              ▼                                ▼
                                   MCPServer                   Distance Score Check
                         ("lookup_medical_term")           (SIMILARITY_THRESHOLD = 0.45)
                                       │                                │
                                       ▼               ┌────────────────┴────────────────┐
                             Structured Definition     ▼                                 ▼
                             + Clinical Metadata     Score <= 0.45                 Score > 0.45
                             (tool_used set)           │                                 │
                                                       ▼                                 ▼
                                             Ollama LLM (qwen3:8b)              Safe Abstention
                                             Grounded Response + Sources       "Insufficient evidence"
```

---

## 3. Router Decisions & Route Classifications

The `AgentRouter` classifies queries into three explicit routes encapsulated in an `AgentDecision` dataclass:

```python
class Route(str, Enum):
    RAG = "rag"
    SAFETY = "safety"
    MCP = "mcp"

@dataclass
class AgentDecision:
    route: Route
    reason: str
    term: str | None = None
```

### Route 1: `Route.SAFETY` (Safety Handling)
- **Triggers**:
  - **Medical Emergencies**: Chest pain, difficulty breathing, loss of consciousness, strokes, severe bleeding, seizures, suicidal ideation, anaphylaxis.
  - **Clinical Action Requests**: Direct disease diagnosis requests ("Can you diagnose me?"), prescription requests ("What medicine should I take?"), and medication discontinuation/alteration requests ("Can I stop taking my pills?").
- **Workflow**:
  - Completely bypasses MCP tools, RAG retrieval, and Ollama inference.
  - Returns a structured `RAGResponse` with `grounded=False`, `abstained=True`, `sources=[]`, `retrieval_info.used=False`, and `tool_used=None`.
  - Delivers a conservative refusal explaining system limitations and advising immediate contact with emergency services or a qualified physician.

### Route 2: `Route.MCP` (Model Context Protocol Reference Tool)
- **Triggers**: Explicit terminology definitions and clinical concept lookups (e.g., "What does hypertension mean?", "Define systolic blood pressure", "What is tachycardia?").
- **Workflow**:
  - Dispatches to `MCPTerminologyClient.lookup_term_sync(term)` across the genuine MCP protocol boundary.
  - Returns structured reference definition, taxonomy category, and clinical standard citation.
  - Sets `grounded=True`, `abstained=False`, `sources=[]`, and `tool_used="lookup_medical_term"`.

### Route 3: `Route.RAG` (Grounded Knowledge Retrieval)
- **Triggers**: General health and medical knowledge questions supported by ingested documentation (e.g., guidelines for hypertension, DASH diet sodium limits, lifestyle modifications).
- **Workflow**:
  - Computes dense query embeddings using local `BAAI/bge-small-en-v1.5`.
  - Queries persistent ChromaDB collection using cosine similarity.
  - Applies similarity threshold check (`SIMILARITY_THRESHOLD = 0.45`).

---

## 4. Layered Abstention Model

The system implements a layered abstention strategy to guarantee factual grounding and patient safety:

1. **Intent-Level Abstention (Router Guard)**:
   - Evaluated at the `AgentRouter`.
   - Rejects clinical claims or emergency queries prior to retrieval (`abstained=True`, `retrieval_info.used=False`).
2. **Tool-Level Abstention (MCP Guard)**:
   - Evaluated when an unknown medical term is queried (`status="not_found"`).
   - Informs the user that the concept is absent from the reference glossary rather than fabricating a definition (`abstained=True`).
3. **Evidence-Level Abstention (Retrieval Guard)**:
   - Evaluated in `RAGEngine` after vector retrieval.
   - If nearest chunk distance exceeds `SIMILARITY_THRESHOLD` (0.45), the system refuses to answer, returning an explicit abstention message ("I don't have enough information in the provided healthcare sources to answer that question.") rather than hallucinating facts.

---

## 5. Agentic Qualification

This implementation qualifies as an agentic orchestration layer because:
- **Dynamic Multi-Capability Selection**: The agent evaluates intent and dynamically decides whether to invoke external tools (MCP), query dense vector indices (RAG), or enforce safety refusals.
- **Formal Protocol Boundary**: MCP tools are registered with explicit JSON-RPC schemas and invoked across a standardized client-server boundary.
- **Explicit Decision Artifacts**: The router outputs structured decision metadata (`route`, `reason`, `term`) before delegating control.
- **Pluggable Delegation**: The router orchestrates specialized sub-systems (`RAGEngine`, `MCPTerminologyClient`, safety guardrails) through clean dependency injection.

---

## 6. Current Limitations

- **Heuristic Pattern Matching**: Intent classification currently relies on normalized regex patterns. Highly convoluted phrasing might evade detection or cause false positives.
- **Stateless Single-Turn Routing**: Routing decisions evaluate single queries independently without conversational context or multi-turn dialogue state.
- **No Multi-Tool Planning Chains**: The agent currently executes single tool invocations rather than chaining multiple interdependent tools sequentially.
