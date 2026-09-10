import logging
import re
from dataclasses import dataclass
from enum import Enum

from app.mcp.client import MCPTerminologyClient
from app.models.rag_models import RAGResponse, RetrievalInfo
from app.rag.engine import RAGEngine

logger = logging.getLogger("healthcare_chatbot.agents")


class Route(str, Enum):
    """Possible execution routes selected by the agent."""

    RAG = "rag"
    SAFETY = "safety"
    MCP = "mcp"


@dataclass
class AgentDecision:
    """Decision produced by the agent router."""

    route: Route
    reason: str
    term: str | None = None


class AgentRouter:
    """Agentic orchestration layer.

    The router dynamically selects among multiple capabilities:
    1. Safety Guardrails: Emergency symptoms or clinical action requests.
    2. Model Context Protocol (MCP) Tools: Authoritative medical terminology lookup.
    3. Grounded RAG: Healthcare knowledge retrieval against ingested documents.
    """

    _EMERGENCY_PATTERNS = (
        r"\b(chest pain|chest pressure|difficulty breathing|trouble breathing)\b",
        r"\b(shortness of breath|cannot breathe|can't breathe|unable to breathe|gasping for air)\b",
        r"\b(severe bleeding|uncontrolled bleeding|coughing (?:up )?blood)\b",
        r"\b(unconscious|passed out|loss of consciousness|fainted)\b",
        r"\b(stroke|face drooping|slurred speech|sudden numbness|paralysis)\b",
        r"\b(seizure|convulsion)\b",
        r"\b(heart attack|cardiac arrest)\b",
        r"\b(suicid|kill myself|self harm|self-harm)\b",
        r"\b(anaphylaxis|severe allergic reaction|choking|throat (?:is )?closing|throat swelling|swelling of the (?:throat|tongue))\b",
        r"\b(drug overdose|overdosed|poisoning|swallowed poison)\b",
    )

    _CLINICAL_ACTION_PATTERNS = (
        r"\b(diagnose|diagnosis)\b",
        r"\b(what disease do i have|what condition do i have|what is wrong with me)\b",
        r"\b(do i have|could i have|am i having a|am i suffering from)\b.*\b(cancer|diabetes|hypertension|covid|tumor|heart attack|stroke|disease|infection)\b",
        r"\b(should i take|what medicine should i take|what medication should i take)\b",
        r"\b(what dosage|what dose|how much)\b.*\b(should i take|to take|of)\b",
        r"\b(stop taking|discontinue)\b.*\b(medicine|medication|prescription|pills?|drugs?|treatment)\b",
        r"\b(stop my medication|change my medication|stop my pills|stop my treatment|change my dose|increase my dose|decrease my dose)\b",
        r"\b(prescribe|prescription)\b",
    )

    _INJECTION_PATTERNS = (
        r"\b(ignore|disregard|override|forget)\b.*\b(previous|all|system)?\s*(instruction|rule|prompt|safety|guardrail)s?\b",
        r"\b(you are now|act as|pretend to be|roleplay as)\b.*\b(unrestricted|jailbreak|doctor|physician|dan|clinician)\b",
        r"\b(bypass\s+(?:safety|guardrails?|filters?))\b",
    )

    _TERMINOLOGY_PATTERNS = (
        r"^what\s+does\s+(.+?)\s+mean\??$",
        r"^what\s+is\s+(?:the\s+)?meaning\s+of\s+(.+?)\??$",
        r"^what\s+is\s+(?:the\s+)?definition\s+of\s+(.+?)\??$",
        r"^define\s+(.+?)\??$",
        r"^definition\s+of\s+(.+?)\??$",
        r"^meaning\s+of\s+(.+?)\??$",
        r"^what\s+is\s+(?:a|an|the)?\s*([a-zA-Z\s\-]+?)\??$",
    )

    def __init__(
        self,
        rag_engine: RAGEngine | None = None,
        mcp_client: MCPTerminologyClient | None = None,
    ):
        self.rag_engine = rag_engine or RAGEngine()
        self.mcp_client = mcp_client or MCPTerminologyClient()

    def classify(self, question: str) -> AgentDecision:
        """Select the execution route for a user question."""
        normalized = " ".join(question.lower().split())

        # 1. SAFETY FIRST: Emergency, clinical action, or prompt injection guardrails take absolute precedence
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

        if self._matches_any(normalized, self._INJECTION_PATTERNS):
            return AgentDecision(
                route=Route.SAFETY,
                reason="Prompt injection or safety guardrail bypass attempt detected.",
            )

        # 2. MCP TOOL: Terminology definition inquiries
        term = self._extract_terminology_term(normalized)
        if term:
            return AgentDecision(
                route=Route.MCP,
                reason=f"Medical terminology lookup for '{term}' routed to MCP tool.",
                term=term,
            )

        # 3. RAG: General healthcare knowledge retrieval
        return AgentDecision(
            route=Route.RAG,
            reason="Healthcare knowledge query routed to grounded RAG.",
        )

    def run(self, question: str) -> RAGResponse:
        """Execute the workflow selected by the agent."""
        decision = self.classify(question)

        logger.info(
            "Agent decision: route=%s reason=%s",
            decision.route.value,
            decision.reason,
        )

        if decision.route == Route.SAFETY:
            return self._safety_response(decision.reason)

        if decision.route == Route.MCP and decision.term:
            return self._mcp_response(decision.term)

        return self.rag_engine.query(question)

    def _extract_terminology_term(self, text: str) -> str | None:
        """Extract a clinical term if the query represents a definition inquiry."""
        # Non-terminology procedural or guidance keywords route to RAG
        non_terminology_keywords = (
            "treatment",
            "procedure",
            "surgery",
            "surgical",
            "management",
            "guideline",
            "cure",
            "lifestyle",
            "help with",
            "prevent",
            "prevention",
            "causes of",
            "symptoms of",
            "how to",
            "should i",
            "can i",
            "modifications",
            "limits",
            "diet sodium",
        )
        if any(kw in text for kw in non_terminology_keywords):
            return None

        for pattern in self._TERMINOLOGY_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                term = match.group(1).strip()
                term = re.sub(r"^(a|an|the)\s+", "", term, flags=re.IGNORECASE).strip()
                # Terms in the glossary are concise concepts (<= 4 words)
                if term and len(term.split()) <= 4:
                    return term
        return None

    @staticmethod
    def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)

    @staticmethod
    def _safety_response(reason: str) -> RAGResponse:
        logger.warning("Safety route selected: %s", reason)

        reason_lower = reason.lower()
        if "emergency" in reason_lower:
            answer = (
                "I am an informational healthcare assistant and cannot evaluate emergency "
                "symptoms or diagnose medical conditions.\n\n"
                "If you or someone nearby is experiencing a potentially serious or life-threatening "
                "emergency (such as acute chest pain, severe shortness of breath, sudden weakness, "
                "or slurred speech), please seek immediate medical attention or call your local "
                "emergency services (such as 911) right away. Do not delay urgent care."
            )
        elif "injection" in reason_lower:
            answer = (
                "I am an informational healthcare assistant and cannot diagnose medical "
                "conditions, prescribe medication, or alter my clinical safety rules.\n\n"
                "System safety guardrails and healthcare guidelines cannot be overridden. "
                "For medical concerns or evaluations, please consult a qualified healthcare professional."
            )
        else:  # Clinical action (diagnosis, prescribing, medication changes, dosage)
            answer = (
                "I am an informational healthcare assistant and cannot diagnose medical "
                "conditions, prescribe medication, recommend specific drug dosages, or tell "
                "you to stop or modify prescribed treatment.\n\n"
                "Please consult a qualified physician or healthcare professional for individualized "
                "medical evaluations, diagnostic testing, and treatment decisions."
            )

        return RAGResponse(
            answer=answer,
            grounded=False,
            abstained=True,
            sources=[],
            retrieval_info=RetrievalInfo(
                used=False,
                results_count=0,
                top_distance=None,
                threshold=0.0,
            ),
            tool_used=None,
        )

    def _mcp_response(self, term: str) -> RAGResponse:
        """Execute medical terminology lookup tool via MCP client bridge."""
        logger.info("Agent executing MCP tool 'lookup_medical_term' for '%s'", term)
        tool_result = self.mcp_client.lookup_term_sync(term)

        if tool_result.get("status") == "found":
            canonical = tool_result.get("canonical_name") or term.title()
            definition = tool_result.get("definition", "")
            category = tool_result.get("category", "General Healthcare")
            reference = tool_result.get("clinical_reference", "Authoritative Reference")
            related = tool_result.get("related_terms", [])

            answer_lines = [
                f"### {canonical}\n",
                f"{definition}\n",
                f"- **Clinical Category**: {category}",
                f"- **Authoritative Reference**: {reference}",
            ]
            if related:
                answer_lines.append(f"- **Related Concepts**: {', '.join(related)}")

            answer_lines.append(
                "\n*Definition retrieved via local MCP Healthcare Reference Tool.*"
            )

            return RAGResponse(
                answer="\n".join(answer_lines),
                grounded=True,
                abstained=False,
                sources=[],
                retrieval_info=RetrievalInfo(
                    used=False,
                    results_count=0,
                    top_distance=None,
                    threshold=0.0,
                ),
                tool_used="lookup_medical_term",
            )

        if tool_result.get("status") == "not_found":
            return RAGResponse(
                answer=(
                    f"The medical term **'{term}'** was not found in the authoritative healthcare reference glossary.\n\n"
                    "For detailed medical questions, please refer to the uploaded clinical guidelines or consult a healthcare professional."
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
                tool_used="lookup_medical_term",
            )

        # Fallback for error/timeout
        error_msg = tool_result.get("message", "Clinical reference tool is temporarily unavailable.")
        return RAGResponse(
            answer=f"Clinical reference lookup failed: {error_msg}",
            grounded=False,
            abstained=True,
            sources=[],
            retrieval_info=RetrievalInfo(
                used=False,
                results_count=0,
                top_distance=None,
                threshold=0.0,
            ),
            tool_used="lookup_medical_term",
        )