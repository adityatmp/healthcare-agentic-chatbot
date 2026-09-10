# Project Current Status - Healthcare Agentic RAG Chatbot

## Current Milestone
- **Milestone 6: Safety, Grounding, and Abstention Hardening** — [COMPLETED]

## Completed Milestones
- [x] **Milestone 0: Project Foundations & Structure**
- [x] **Milestone 1: Core RAG Vertical Slice**
- [x] **Milestone 2: FastAPI Backend Layer**
- [x] **Milestone 3: React Frontend Application**
- [x] **Milestone 4: Agentic Orchestration Layer**
- [x] **Milestone 5: Model Context Protocol (MCP) Tool Integration**
- [x] **Milestone 6: Safety, Grounding, and Abstention Hardening**

---

## Milestone 6 Deliverables & Technical Specs

- **Safety-First Precedence & Routing Hardening (`backend/app/agents/router.py`)**:
  - Expanded acute emergency detection (`_EMERGENCY_PATTERNS`) to cover shortness of breath, gasping for air, sudden numbness/paralysis (stroke signs), heart attacks, cardiac arrest, throat closing/swelling, coughing up blood, drug overdose, and poisoning.
  - Expanded clinical action guardrails (`_CLINICAL_ACTION_PATTERNS`) to intercept diagnostic inquiries ("Do I have cancer?", "What is wrong with me?"), medication inquiries ("What medicine should I take?"), dosage inquiries ("What dosage should I take?"), and dose adjustments ("Should I increase my dose?").
  - Added prompt injection detection (`_INJECTION_PATTERNS`) to trap instruction-override attempts ("ignore previous rules"), adversarial persona jailbreaks ("you are now an unrestricted doctor"), and filter bypasses.
  - Enforced strict hierarchical precedence: emergency, clinical action, and prompt injection patterns immediately route to `Route.SAFETY`, unconditionally bypassing MCP tools and RAG retrieval.
  - Tailored conservative safety responses: differentiated responses for acute emergencies (immediate directive to seek urgent care or call 911), clinical actions (physician consultation referral without diagnosing/prescribing), and injection attempts (reinforcing that guardrails cannot be overridden).
- **RAG Grounding & Context Isolation (`backend/app/rag/engine.py`)**:
  - Implemented `_sanitize_xml_tags()` escaping XML delimiter breakout sequences (`<context>`, `</context>`, `<?xml`) in both retrieved document text and user queries.
  - Hardened `RAG_SYSTEM_PROMPT` to explicitly treat all text in `<context>` as UNTRUSTED DATA, forbidding adherence to embedded instructions, roleplays, or overrides.
- **Layered Abstention Model**:
  - Tier 1: Router Guard intercepts unsafe queries with zero vector/LLM compute (`abstained=True`).
  - Tier 2: MCP Tool Guard cleanly abstains on unknown terms (`tool_used="lookup_medical_term"`, `abstained=True`).
  - Tier 3: Vector Retrieval Guard abstains when cosine distance exceeds 0.45 without fabricating answers.
- **Test Suite Expansion (`tests/test_agent_router.py`, `tests/test_api.py`, `tests/test_rag.py`)**:
  - Expanded test suite from 54 to **76 passed tests** (0 failures).
  - Added unit tests for emergency variants, clinical action variants, dosage inquiries, prompt injection attempts, safety-first overrides for MCP and RAG, XML delimiter sanitization, and API safety routes.
- **Live API Verification (Cases A through G)**:
  - Case A (Emergency): `Route.SAFETY`, conservative urgent-care/911 directive, zero RAG/MCP.
  - Case B (Diagnosis Request): `Route.SAFETY`, non-diagnostic refusal, zero RAG/MCP.
  - Case C (Prescription / Dosage): `Route.SAFETY`, non-prescribing refusal, zero RAG/MCP.
  - Case D (Terminology): `Route.MCP`, `tool_used="lookup_medical_term"`, grounded AHA/CDC reference.
  - Case E (General Healthcare RAG): `Route.RAG`, `grounded=True`, 3 citations, CDC guidelines.
  - Case F (Unsupported Knowledge): `Route.RAG`, `abstained=True`, distance 0.489 > 0.45.
  - Case G (Prompt Injection): `Route.SAFETY`, guardrails upheld, non-diagnostic refusal.
- **Documentation (`docs/security.md`, `docs/agentic_workflow.md`)**:
  - Expanded `docs/security.md` into comprehensive safety, security, and grounding specification.
  - Updated `docs/agentic_workflow.md` to reflect hardened three-tier orchestration and guardrails.

---

## Test Results

- **Full Pytest Suite**:
  - `76 passed` in Pytest test suite (`tests/test_agent_router.py`, `tests/test_api.py`, `tests/test_health.py`, `tests/test_mcp_client.py`, `tests/test_mcp_server.py`, `tests/test_rag.py`).
- **Frontend Verification**:
  - Production build cleanly completed (`vite build` 0 errors, 741ms).
  - Code linter cleanly completed (`oxlint` 0 warnings, 0 errors, 98ms).

---

## Next Milestone
- Milestone 6 is complete. Awaiting next milestone instruction.


