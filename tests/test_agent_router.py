"""
Tests for the AgentRouter (backend/app/agents/router.py).

Covers:
- Normal healthcare question routes to RAG
- Emergency question routes to SAFETY
- Diagnosis request routes to SAFETY
- Prescription / medication-change request routes to SAFETY
- Safety route returns a valid RAGResponse (grounded=False, abstained=True)
- Safety route does NOT call the RAG engine
- RAG route DOES call the RAG engine and returns its result
- Mixed-case and extra whitespace queries still classify correctly
"""

import pytest
from app.agents.router import AgentRouter, AgentDecision, Route
from app.models.rag_models import RAGResponse, RetrievalInfo


# ---------------------------------------------------------------------------
# Shared fake RAG engine
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


# ---------------------------------------------------------------------------
# Classification tests (classify() only)
# ---------------------------------------------------------------------------

def test_normal_healthcare_question_routes_to_rag():
    """Generic healthcare knowledge question should go to RAG."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("What lifestyle changes can help with high blood pressure?")
    assert decision.route == Route.RAG


def test_emergency_question_routes_to_safety():
    """Chest-pain/breathing emergency should route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("I am having severe chest pain and difficulty breathing.")
    assert decision.route == Route.SAFETY


def test_diagnosis_request_routes_to_safety():
    """Explicit diagnosis request should route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("Can you diagnose what disease I have?")
    assert decision.route == Route.SAFETY


def test_prescription_request_routes_to_safety():
    """'Should I take this medication' requests must route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("What medicine should I take for my headaches?")
    assert decision.route == Route.SAFETY


def test_medication_discontinuation_routes_to_safety():
    """Requests to stop prescribed medication must route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("Can I stop taking my medication for high blood pressure?")
    assert decision.route == Route.SAFETY


def test_prescribe_keyword_routes_to_safety():
    """The word 'prescribe' alone should trigger SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("Can you prescribe something for my arthritis pain?")
    assert decision.route == Route.SAFETY


# ---------------------------------------------------------------------------
# Mixed-case and whitespace normalization
# ---------------------------------------------------------------------------

def test_emergency_mixed_case_routes_to_safety():
    """Classification must be case-insensitive."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("I Am Having CHEST PAIN Right Now!")
    assert decision.route == Route.SAFETY


def test_extra_whitespace_normalized_correctly():
    """Extra internal whitespace must not break pattern matching."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("I  am   having   severe   chest   pain.")
    assert decision.route == Route.SAFETY


def test_diagnosis_mixed_case_routes_to_safety():
    """Diagnosis keyword should match regardless of casing."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("Please DIAGNOSE my condition.")
    assert decision.route == Route.SAFETY


def test_normal_question_leading_trailing_whitespace():
    """Leading/trailing whitespace should not affect RAG routing."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("  What is hypertension?  ")
    assert decision.route == Route.RAG


# ---------------------------------------------------------------------------
# run() execution tests — verify correct delegate is called
# ---------------------------------------------------------------------------

def test_rag_route_calls_rag_engine_and_returns_result():
    """Normal question: run() must call rag_engine.query() and return its result."""
    fake_rag = FakeRAGEngine()
    router = AgentRouter(rag_engine=fake_rag)

    result = router.run("What is hypertension?")

    assert fake_rag._call_count == 1
    assert fake_rag.called_with == "What is hypertension?"
    assert result.answer == "RAG_RESULT"
    assert result.grounded is True
    assert result.abstained is False


def test_safety_route_does_not_call_rag_engine():
    """Safety question: run() must NOT call rag_engine.query()."""
    fake_rag = FakeRAGEngine()
    router = AgentRouter(rag_engine=fake_rag)

    result = router.run("I'm having a seizure right now.")

    assert fake_rag._call_count == 0, "RAG engine must not be called on safety route"


def test_safety_route_returns_valid_ragresponse():
    """Safety route must return a properly structured RAGResponse."""
    fake_rag = FakeRAGEngine()
    router = AgentRouter(rag_engine=fake_rag)

    result = router.run("Can you diagnose my symptoms?")

    assert isinstance(result, RAGResponse)
    assert result.grounded is False
    assert result.abstained is True
    assert result.sources == []
    assert result.retrieval_info.used is False
    assert result.retrieval_info.results_count == 0
    # threshold must be a float (not None) — RetrievalInfo.threshold is float
    assert isinstance(result.retrieval_info.threshold, float)


def test_safety_response_does_not_contain_fabricated_diagnosis():
    """Safety answer must not mention diagnosis or treatment instructions."""
    fake_rag = FakeRAGEngine()
    router = AgentRouter(rag_engine=fake_rag)

    result = router.run("What disease do I have based on my symptoms?")

    answer_lower = result.answer.lower()
    # Must redirect to professional care, not diagnose
    assert "diagnose" not in answer_lower or "cannot diagnose" in answer_lower
    assert "consult" in answer_lower or "healthcare professional" in answer_lower or "medical" in answer_lower


def test_agent_decision_has_reason():
    """AgentDecision.reason must be a non-empty string."""
    router = AgentRouter(rag_engine=FakeRAGEngine())

    rag_decision = router.classify("What is the DASH diet?")
    assert rag_decision.reason and len(rag_decision.reason) > 0

    safety_decision = router.classify("I have chest pain.")
    assert safety_decision.reason and len(safety_decision.reason) > 0


def test_anaphylaxis_emergency_routes_to_safety():
    """Severe allergic reaction/anaphylaxis must route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("Help, I think I am having anaphylaxis!")
    assert decision.route == Route.SAFETY
    assert "emergency" in decision.reason.lower()


def test_stop_pills_clinical_action_routes_to_safety():
    """Requests to stop pills or treatment must route to SAFETY."""
    router = AgentRouter(rag_engine=FakeRAGEngine())
    decision = router.classify("Should I stop taking my pills if I feel better?")
    assert decision.route == Route.SAFETY


def test_route_enum_values():
    """Verify Route enum contains expected string values."""
    assert Route.RAG.value == "rag"
    assert Route.SAFETY.value == "safety"