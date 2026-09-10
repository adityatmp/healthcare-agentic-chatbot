import logging
import re
from dataclasses import dataclass
from enum import Enum

from app.rag.engine import RAGEngine

logger = logging.getLogger("healthcare_chatbot.agents")


class Route(str, Enum):
    """Possible execution routes selected by the agent."""

    RAG = "rag"
    SAFETY = "safety"


@dataclass
class AgentDecision:
    """Decision produced by the lightweight agent router."""

    route: Route
    reason: str


class AgentRouter:
    """
    Lightweight agentic orchestration layer.

    The router decides whether a request should:
    - go through the grounded RAG workflow, or
    - receive a conservative safety response.

    Keeping this decision explicit makes the workflow easy to
    understand, test, and extend with MCP tools later.
    """

    _EMERGENCY_PATTERNS = (
        r"\b(chest pain|chest pressure|difficulty breathing|trouble breathing)\b",
        r"\b(cannot breathe|can't breathe|unable to breathe)\b",
        r"\b(severe bleeding|uncontrolled bleeding)\b",
        r"\b(unconscious|passed out|loss of consciousness)\b",
        r"\b(stroke|face drooping|slurred speech)\b",
        r"\b(seizure|convulsion)\b",
        r"\b(suicid|kill myself|self harm|self-harm)\b",
        r"\b(anaphylaxis|severe allergic reaction|choking)\b",
    )

    _CLINICAL_ACTION_PATTERNS = (
        r"\b(diagnose|diagnosis)\b",
        r"\b(what disease do i have|what condition do i have)\b",
        r"\b(should i take|what medicine should i take)\b",
        r"\b(what medication should i take)\b",
        r"\b(stop taking|discontinue)\b.*\b(medicine|medication|prescription|pills?|drugs?|treatment)\b",
        r"\b(stop my medication|change my medication|stop my pills|stop my treatment)\b",
        r"\b(prescribe|prescription)\b",
    )

    def __init__(self, rag_engine: RAGEngine | None = None):
        self.rag_engine = rag_engine or RAGEngine()

    def classify(self, question: str) -> AgentDecision:
        """
        Select the execution route for a user question.
        """
        normalized = " ".join(question.lower().split())

        if self._matches_any(normalized, self._EMERGENCY_PATTERNS):
            return AgentDecision(
                route=Route.SAFETY,
                reason="Potential emergency/urgent medical situation detected.",
            )

        if self._matches_any(normalized, self._CLINICAL_ACTION_PATTERNS):
            return AgentDecision(
                route=Route.SAFETY,
                reason="Question requests diagnosis, prescribing, or medication changes.",
            )

        return AgentDecision(
            route=Route.RAG,
            reason="Healthcare knowledge query routed to grounded RAG.",
        )

    def run(self, question: str):
        """
        Execute the workflow selected by the agent.
        """
        decision = self.classify(question)

        logger.info(
            "Agent decision: route=%s reason=%s",
            decision.route.value,
            decision.reason,
        )

        if decision.route == Route.SAFETY:
            return self._safety_response(decision.reason)

        return self.rag_engine.query(question)

    @staticmethod
    def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

    @staticmethod
    def _safety_response(reason: str):
        from app.models.rag_models import RAGResponse, RetrievalInfo

        logger.warning("Safety route selected: %s", reason)

        return RAGResponse(
            answer=(
                "I’m an informational healthcare assistant and cannot diagnose "
                "medical conditions, prescribe medication, or tell you to stop "
                "prescribed treatment.\n\n"
                "If you are experiencing a potentially serious or emergency "
                "symptom, seek urgent medical care or contact your local emergency "
                "services. For non-emergency medical decisions, please consult a "
                "qualified healthcare professional."
            ),
            grounded=False,
            abstained=True,
            sources=[],
            retrieval_info=RetrievalInfo(
                used=False,
                results_count=0,
                top_distance=None,
                threshold=0.0,
            ),
        )