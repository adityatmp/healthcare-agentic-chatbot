"""
Tests for the AgentRouter (backend/app/agents/router.py).

Covers:
- Normal healthcare question routes to RAG
- Emergency question routes to SAFETY
- Diagnosis request routes to SAFETY
- Prescription / medication-change request routes to SAFETY
- Terminology definition questions route to MCP
- Safety-first precedence over MCP terminology queries
- Safety route returns a valid RAGResponse (grounded=False, abstained=True)
- Safety route does NOT call the RAG engine or MCP client
- RAG route DOES call the RAG engine and returns its result
- MCP route DOES call the MCP client and returns structured definition with tool_used
- Mixed-case and extra whitespace queries classify correctly
"""

import pytest
from app.agents.router import AgentRouter, AgentDecision, Route
from app.models.rag_models import RAGResponse, RetrievalInfo


# ---------------------------------------------------------------------------
# Shared fake RAG engine & Fake MCP client
# ---------------------------------------------------------------------------

class FakeRAGEngine:
    """Fake RAGEngine that records calls without hitting ChromaDB or Ollama."""

    def __init__(self):
        self.called_with: str | None = None
        self._call_count = 0

    def query(self, question: str) -> RAGResponse:
        self.called_with = question
        self._call_count += 1
        return RAGResponse(
            answer="RAG_RESULT",
            grounded=True,
            abstained=False,
            sources=[],
            retrieval_info=RetrievalInfo(
                used=True,
                results_count=1,
                top_distance=0.15,
                threshold=0.4,
            ),
        )


class FakeMCPClient:
    """Fake MCPTerminologyClient for recording router MCP tool calls."""

    def __init__(self, response: dict | None = None):
        self.called_with: str | None = None
        self._call_count = 0
        self.response = response or {
            "term": "hypertension",
            "normalized_term": "hypertension",
            "canonical_name": "Hypertension (High Blood Pressure)",
            "definition": "High blood pressure condition.",
            "category": "Cardiovascular",
            "clinical_reference": "AHA Guidelines",
            "related_terms": ["blood pressure"],
            "status": "found",
        }

    def lookup_term_sync(self, term: str) -> dict:
        self.called_with = term
        self._call_count += 1
        return self.response


# ---------------------------------------------------------------------------
# Classification tests (classify() only)
# ---------------------------------------------------------------------------

def test_normal_healthcare_question_routes_to_rag():
    """Generic healthcare knowledge question should go to RAG."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("What lifestyle changes can help with high blood pressure?")
    assert decision.route == Route.RAG


def test_emergency_question_routes_to_safety():
    """Chest-pain/breathing emergency should route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("I am having severe chest pain and difficulty breathing.")
    assert decision.route == Route.SAFETY


def test_diagnosis_request_routes_to_safety():
    """Explicit diagnosis request should route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("Can you diagnose what disease I have?")
    assert decision.route == Route.SAFETY


def test_prescription_request_routes_to_safety():
    """'Should I take this medication' requests must route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("What medicine should I take for my headaches?")
    assert decision.route == Route.SAFETY


def test_medication_discontinuation_routes_to_safety():
    """Requests to stop prescribed medication must route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("Can I stop taking my medication for high blood pressure?")
    assert decision.route == Route.SAFETY


def test_prescribe_keyword_routes_to_safety():
    """The word 'prescribe' alone should trigger SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("Can you prescribe something for my arthritis pain?")
    assert decision.route == Route.SAFETY


def test_anaphylaxis_emergency_routes_to_safety():
    """Severe allergic reaction/anaphylaxis must route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("Help, I think I am having anaphylaxis!")
    assert decision.route == Route.SAFETY
    assert "emergency" in decision.reason.lower()


def test_stop_pills_clinical_action_routes_to_safety():
    """Requests to stop pills or treatment must route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("Should I stop taking my pills if I feel better?")
    assert decision.route == Route.SAFETY


# ---------------------------------------------------------------------------
# MCP Terminology Classification Tests
# ---------------------------------------------------------------------------

def test_terminology_what_does_mean_routes_to_mcp():
    """'What does hypertension mean?' should route to MCP."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("What does hypertension mean?")
    assert decision.route == Route.MCP
    assert decision.term == "hypertension"


def test_terminology_define_routes_to_mcp():
    """'Define systolic blood pressure.' should route to MCP."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("Define systolic blood pressure.")
    assert decision.route == Route.MCP
    assert "systolic blood pressure" in decision.term


def test_terminology_what_is_routes_to_mcp():
    """'What is tachycardia?' should route to MCP."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("What is tachycardia?")
    assert decision.route == Route.MCP
    assert decision.term == "tachycardia"


def test_terminology_meaning_of_routes_to_mcp():
    """'What is the meaning of arrhythmia?' should route to MCP."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("What is the meaning of arrhythmia?")
    assert decision.route == Route.MCP
    assert decision.term == "arrhythmia"


def test_procedural_what_is_question_routes_to_rag():
    """'What is the surgical treatment for acute appendicitis in adults?' routes to RAG, not MCP."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("What is the surgical treatment for acute appendicitis in adults?")
    assert decision.route == Route.RAG


def test_emergency_with_terminology_pattern_overrides_to_safety():
    """Safety rules take precedence: 'I have chest pain, what is the definition?' routes to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("I have severe chest pain, what does it mean?")
    assert decision.route == Route.SAFETY


def test_diagnosis_with_terminology_pattern_overrides_to_safety():
    """Diagnosis rule takes precedence over terminology lookup."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("Can you diagnose what disease I have from tachycardia?")
    assert decision.route == Route.SAFETY


# ---------------------------------------------------------------------------
# Mixed-case and whitespace normalization
# ---------------------------------------------------------------------------

def test_emergency_mixed_case_routes_to_safety():
    """Classification must be case-insensitive."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("I Am Having CHEST PAIN Right Now!")
    assert decision.route == Route.SAFETY


def test_extra_whitespace_normalized_correctly():
    """Extra internal whitespace must not break pattern matching."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("I  am   having   severe   chest   pain.")
    assert decision.route == Route.SAFETY


def test_terminology_mixed_case_and_whitespace():
    """Terminology queries should normalize mixed-case and whitespace."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("   What   Does   HYPERTENSION   Mean?   ")
    assert decision.route == Route.MCP
    assert decision.term == "hypertension"


def test_normal_question_leading_trailing_whitespace():
    """Leading/trailing whitespace should not affect RAG routing."""
    router = AgentRouter(rag_engine=FakeRAGEngine(), mcp_client=FakeMCPClient())
    decision = router.classify("  What lifestyle changes help with high blood pressure?  ")
    assert decision.route == Route.RAG


# ---------------------------------------------------------------------------
# run() execution tests — verify correct delegate is called
# ---------------------------------------------------------------------------

def test_rag_route_calls_rag_engine_and_returns_result():
    """Normal question: run() must call rag_engine.query() and return its result."""
    fake_rag = FakeRAGEngine()
    fake_mcp = FakeMCPClient()
    router = AgentRouter(rag_engine=fake_rag, mcp_client=fake_mcp)

    result = router.run("What lifestyle changes help with high blood pressure?")

    assert fake_rag._call_count == 1
    assert fake_mcp._call_count == 0
    assert result.answer == "RAG_RESULT"
    assert result.grounded is True
    assert result.abstained is False


def test_safety_route_does_not_call_rag_or_mcp():
    """Safety question: run() must NOT call rag_engine or mcp_client."""
    fake_rag = FakeRAGEngine()
    fake_mcp = FakeMCPClient()
    router = AgentRouter(rag_engine=fake_rag, mcp_client=fake_mcp)

    result = router.run("I'm having a seizure right now.")

    assert fake_rag._call_count == 0
    assert fake_mcp._call_count == 0
    assert result.grounded is False
    assert result.abstained is True


def test_mcp_route_calls_mcp_client_and_returns_tool_used():
    """Terminology question: run() calls mcp_client and returns structured RAGResponse."""
    fake_rag = FakeRAGEngine()
    fake_mcp = FakeMCPClient()
    router = AgentRouter(rag_engine=fake_rag, mcp_client=fake_mcp)

    result = router.run("What does hypertension mean?")

    assert fake_rag._call_count == 0
    assert fake_mcp._call_count == 1
    assert fake_mcp.called_with == "hypertension"
    assert result.grounded is True
    assert result.abstained is False
    assert result.tool_used == "lookup_medical_term"
    assert "Hypertension" in result.answer
    assert "Cardiovascular" in result.answer


def test_mcp_route_unknown_term_abstains():
    """Unknown term handled via MCP returns clean abstention."""
    fake_rag = FakeRAGEngine()
    fake_mcp = FakeMCPClient(response={"status": "not_found", "message": "Not found"})
    router = AgentRouter(rag_engine=fake_rag, mcp_client=fake_mcp)

    result = router.run("What does unknownclinicalterm mean?")

    assert result.grounded is False
    assert result.abstained is True
    assert result.tool_used == "lookup_medical_term"
    assert "not found" in result.answer.lower()


def test_route_enum_values():
    """Verify Route enum contains expected string values."""
    assert Route.RAG.value == "rag"
    assert Route.SAFETY.value == "safety"
    assert Route.MCP.value == "mcp"