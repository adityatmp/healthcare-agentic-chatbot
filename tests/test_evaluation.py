"""
Tests for Evaluation Framework (scripts/evaluate.py and eval/dataset.json).

Covers:
- Dataset integrity and schema validation
- Metric computation logic (routing, retrieval, abstention, citations)
- Separation margin calculation in threshold analysis
- Evaluation case execution using mock engines
"""

import pytest
from scripts.evaluate import load_dataset, compute_metrics, evaluate_case
from app.agents.router import AgentRouter
from app.models.rag_models import RAGResponse, RetrievalInfo, SourceMetadata


def test_evaluation_dataset_schema_and_size():
    """Verify eval/dataset.json contains required fields and all 6 capability groups."""
    cases = load_dataset("eval/dataset.json")
    assert len(cases) >= 20, "Evaluation dataset must contain at least 20 curated cases"

    required_keys = {
        "id",
        "group",
        "question",
        "expected_route",
        "expected_grounded",
        "expected_abstained",
    }
    groups_found = set()

    for case in cases:
        assert required_keys.issubset(case.keys()), f"Missing keys in case {case.get('id')}"
        assert case["expected_route"] in ("rag", "safety", "mcp")
        assert isinstance(case["expected_grounded"], bool)
        assert isinstance(case["expected_abstained"], bool)
        groups_found.add(case["group"])

    # Ensure all required evaluation groups are covered
    expected_groups = {
        "rag_supported",
        "rag_unsupported",
        "mcp_terminology",
        "safety_emergency",
        "safety_clinical_action",
        "safety_prompt_injection",
        "safety_precedence",
    }
    assert expected_groups.issubset(groups_found)


def test_metric_computation_deterministic():
    """Verify compute_metrics calculates correct rates from synthetic results."""
    mock_results = [
        # 1. RAG supported grounded
        {
            "id": "1",
            "group": "rag_supported",
            "expected": {"route": "rag", "grounded": True, "abstained": False, "tool": None},
            "actual": {"route": "rag", "grounded": True, "abstained": False, "tool": None, "top_distance": 0.15},
            "checks": {
                "route_correct": True,
                "grounded_correct": True,
                "abstained_correct": True,
                "tool_correct": True,
                "citations_correct": True,
                "passed": True,
            },
            "latency_ms": 100.0,
        },
        # 2. RAG unsupported abstained
        {
            "id": "2",
            "group": "rag_unsupported",
            "expected": {"route": "rag", "grounded": False, "abstained": True, "tool": None},
            "actual": {"route": "rag", "grounded": False, "abstained": True, "tool": None, "top_distance": 0.50},
            "checks": {
                "route_correct": True,
                "grounded_correct": True,
                "abstained_correct": True,
                "tool_correct": True,
                "citations_correct": True,
                "passed": True,
            },
            "latency_ms": 10.0,
        },
        # 3. Safety emergency
        {
            "id": "3",
            "group": "safety_emergency",
            "expected": {"route": "safety", "grounded": False, "abstained": True, "tool": None},
            "actual": {"route": "safety", "grounded": False, "abstained": True, "tool": None, "top_distance": None},
            "checks": {
                "route_correct": True,
                "grounded_correct": True,
                "abstained_correct": True,
                "tool_correct": True,
                "citations_correct": True,
                "passed": True,
            },
            "latency_ms": 5.0,
        },
        # 4. MCP terminology
        {
            "id": "4",
            "group": "mcp_terminology",
            "expected": {"route": "mcp", "grounded": True, "abstained": False, "tool": "lookup_medical_term"},
            "actual": {"route": "mcp", "grounded": True, "abstained": False, "tool": "lookup_medical_term", "top_distance": None},
            "checks": {
                "route_correct": True,
                "grounded_correct": True,
                "abstained_correct": True,
                "tool_correct": True,
                "citations_correct": True,
                "passed": True,
            },
            "latency_ms": 8.0,
        },
    ]

    metrics = compute_metrics(mock_results, similarity_threshold=0.45)

    assert metrics["summary"]["total_cases"] == 4
    assert metrics["summary"]["overall_accuracy"] == 1.0
    assert metrics["summary"]["route_accuracy"] == 1.0
    assert metrics["rag"]["retrieval_hit_rate"] == 1.0
    assert metrics["rag"]["grounded_answer_rate"] == 1.0
    assert metrics["rag"]["abstention_correctness"] == 1.0
    assert metrics["mcp"]["tool_invocation_rate"] == 1.0
    assert metrics["safety"]["emergency_accuracy"] == 1.0

    # Threshold margin: min(unsupported=0.50) - max(supported=0.15) = 0.35
    assert metrics["threshold_analysis"]["separation_margin"] == 0.35
    assert metrics["latency_ms"]["overall"]["mean"] > 0
