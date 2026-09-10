# Agentic Workflow & Orchestration Architecture

## 1. Architectural Overview & Motivation

In a high-stakes domain like healthcare, feeding every user query directly into a generic Retrieval-Augmented Generation (RAG) pipeline is unsafe and inefficient. An orchestration layer acts as an explicit decision boundary that inspects incoming user queries before initiating vector retrieval or LLM inference.

### Why an Orchestration Layer Exists
- **Safety Gatekeeping**: Critical medical emergencies, direct diagnosis requests, and medication alteration inquiries must never be handled by open-ended text generation.
- **Resource Efficiency**: Bypassing embedding generation and vector database queries for queries that cannot safely be answered saves computational overhead.
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
                 ┌─────────────────┴─────────────────┐
                 ▼                                   ▼
        [Route.SAFETY]                         [Route.RAG]
    Emergency / Clinical Claim             General Healthcare Query
                 │                                   │
                 ▼                                   ▼
    Conservative Refusal                    RAG Engine Retrieval
    - Grounded: False                       (Embedding + ChromaDB)
    - Abstained: True                                │
    - Zero Vector/LLM compute                        ▼
                                            Distance Score Check
                                        (SIMILARITY_THRESHOLD = 0.45)
                                                     │
                                   ┌─────────────────┴─────────────────┐
                                   ▼                                   ▼
                          Distance <= 0.45                    Distance > 0.45
                                   │                                   │
                                   ▼                                   ▼
                         Ollama LLM (qwen3:8b)                Safe Abstention
                         Grounded Response + Sources         "Insufficient evidence..."
```

---

## 3. Router Decisions & Route Classifications

The `AgentRouter` classifies queries into two explicit routes encapsulated in an `AgentDecision` dataclass:

```python
class Route(str, Enum):
    RAG = "rag"
    SAFETY = "safety"

@dataclass
class AgentDecision:
    route: Route
    reason: str
```

### Route 1: `Route.SAFETY` (Safety Handling)
- **Triggers**:
  - **Medical Emergencies**: Chest pain, difficulty breathing, loss of consciousness, strokes, severe bleeding, seizures, suicidal ideation, anaphylaxis.
  - **Clinical Action Requests**: Direct disease diagnosis requests ("Can you diagnose me?"), prescription requests ("What medicine should I take?"), and medication discontinuation/alteration requests ("Can I stop taking my pills?").
- **Workflow**:
  - Completely bypasses RAG retrieval and Ollama inference.
  - Returns a structured `RAGResponse` with `grounded=False`, `abstained=True`, `sources=[]`, and `retrieval_info.used=False`.
  - Delivers a conservative refusal explaining system limitations and advising immediate contact with emergency services or a qualified physician.

### Route 2: `Route.RAG` (Grounded Knowledge Retrieval)
- **Triggers**: General health and medical knowledge questions supported by ingested documentation (e.g., guidelines for hypertension, DASH diet sodium limits, lifestyle modifications).
- **Workflow**:
  - Computes dense query embeddings using local `BAAI/bge-small-en-v1.5`.
  - Queries persistent ChromaDB collection using cosine similarity.
  - Applies similarity threshold check.

---

## 4. Two-Tier Abstention Model

The system implements a layered abstention strategy to guarantee factual grounding and patient safety:

1. **Intent-Level Abstention (Router Guard)**:
   - Evaluated at the `AgentRouter`.
   - Rejects clinical claims or emergency queries prior to retrieval (`abstained=True`, `retrieval_info.used=False`).
2. **Evidence-Level Abstention (Retrieval Guard)**:
   - Evaluated in `RAGEngine` after vector retrieval.
   - If nearest chunk distance exceeds `SIMILARITY_THRESHOLD` (0.45), the system refuses to answer, returning an explicit abstention message ("I don't have enough information in the provided healthcare sources to answer that question.") rather than hallucinating facts.

---

## 5. Agentic Qualification

This implementation qualifies as an agentic orchestration layer because:
- **Separation of Intent from Execution**: The workflow is not a fixed, monolithic script. Execution branches dynamically based on evaluated intent.
- **Explicit Decision Artifacts**: The router outputs structured decision metadata (`route` and `reason`) before delegating control.
- **Pluggable Delegation**: The router orchestrates specialized sub-systems (`RAGEngine`, safety guardrails, and future tool integrations like MCP) through clean dependency injection.

---

## 6. Current Limitations

- **Heuristic Pattern Matching**: Intent classification currently relies on normalized regex patterns. Highly convoluted phrasing might evade detection or cause false positives.
- **Stateless Single-Turn Routing**: Routing decisions evaluate single queries independently without conversational context or multi-turn dialogue state.
- **No Autonomous Iteration**: The router does not perform autonomous multi-step reasoning, query reformulation, or self-correction loops. These capabilities are intentionally deferred to future milestones.
