"""
Reproducible Evaluation Suite for Healthcare Agentic Chatbot.

Evaluates:
1. Agent Routing Accuracy (Safety, MCP, RAG, Precedence)
2. RAG Retrieval Hit Rate, Groundedness, and Abstention Correctness
3. Citation & Source Validity
4. MCP Protocol Execution & Unknown Term Handling
5. Similarity Threshold Gating (Distance distributions for supported vs unsupported)
6. Latency Analysis per Route (Mean, Median)

Usage:
    python -m scripts.evaluate [--dataset eval/dataset.json] [--output-dir eval_results]
"""

import argparse
import json
import logging
import os
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List

# Suppress verbose loggers during evaluation runs
logging.basicConfig(level=logging.WARNING)
for log_name in ("healthcare_chatbot", "httpx", "chromadb", "sentence_transformers"):
    logging.getLogger(log_name).setLevel(logging.WARNING)

from app.agents.router import AgentRouter, Route
from app.mcp.client import MCPTerminologyClient
from app.rag.engine import RAGEngine


def load_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Load evaluation test cases from JSON dataset."""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at '{dataset_path}'")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_case(
    router: AgentRouter,
    case: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a single evaluation case through the agent router and measure fidelity."""
    question = case["question"]
    expected_route = case["expected_route"]
    expected_grounded = case["expected_grounded"]
    expected_abstained = case["expected_abstained"]
    expected_tool = case.get("expected_tool")
    expected_sources = case.get("expected_sources", [])

    # Measure routing classification
    decision = router.classify(question)
    actual_route = decision.route.value

    # Measure end-to-end execution and latency
    start_time = time.perf_counter()
    response = router.run(question)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    actual_grounded = response.grounded
    actual_abstained = response.abstained
    actual_tool = response.tool_used
    actual_sources = [s.document for s in response.sources]

    # Evaluate correctness criteria
    route_correct = actual_route == expected_route
    grounded_correct = actual_grounded == expected_grounded
    abstained_correct = actual_abstained == expected_abstained
    tool_correct = actual_tool == expected_tool

    # Citation validation:
    # Grounded RAG queries must have document sources; safety, MCP, and abstained queries must have 0 document citations
    if expected_route == "rag" and expected_grounded:
        citations_correct = len(actual_sources) > 0 and any(
            src in expected_sources for src in actual_sources
        )
    else:
        citations_correct = len(actual_sources) == 0

    top_distance = response.retrieval_info.top_distance if response.retrieval_info.used else None

    return {
        "id": case["id"],
        "group": case["group"],
        "question": question,
        "expected": {
            "route": expected_route,
            "grounded": expected_grounded,
            "abstained": expected_abstained,
            "tool": expected_tool,
        },
        "actual": {
            "route": actual_route,
            "grounded": actual_grounded,
            "abstained": actual_abstained,
            "tool": actual_tool,
            "sources": actual_sources,
            "top_distance": top_distance,
        },
        "checks": {
            "route_correct": route_correct,
            "grounded_correct": grounded_correct,
            "abstained_correct": abstained_correct,
            "tool_correct": tool_correct,
            "citations_correct": citations_correct,
            "passed": (
                route_correct
                and grounded_correct
                and abstained_correct
                and tool_correct
                and citations_correct
            ),
        },
        "latency_ms": round(elapsed_ms, 2),
    }


def compute_metrics(results: List[Dict[str, Any]], similarity_threshold: float) -> Dict[str, Any]:
    """Compute quantitative benchmark metrics across evaluation groups."""
    total = len(results)
    if total == 0:
        return {}

    # 1. Routing Metrics
    route_correct_count = sum(1 for r in results if r["checks"]["route_correct"])
    safety_cases = [r for r in results if r["expected"]["route"] == "safety"]
    mcp_cases = [r for r in results if r["expected"]["route"] == "mcp"]
    rag_cases = [r for r in results if r["expected"]["route"] == "rag"]

    safety_route_accuracy = (
        sum(1 for r in safety_cases if r["checks"]["route_correct"]) / len(safety_cases)
        if safety_cases
        else 1.0
    )
    mcp_route_accuracy = (
        sum(1 for r in mcp_cases if r["checks"]["route_correct"]) / len(mcp_cases)
        if mcp_cases
        else 1.0
    )
    rag_route_accuracy = (
        sum(1 for r in rag_cases if r["checks"]["route_correct"]) / len(rag_cases)
        if rag_cases
        else 1.0
    )

    # 2. RAG Grounding & Retrieval Metrics
    rag_supported = [r for r in results if r["group"] == "rag_supported"]
    rag_unsupported = [r for r in results if r["group"] == "rag_unsupported"]

    # Retrieval hit rate: supported questions where top_distance <= threshold
    retrieval_hits = [
        r
        for r in rag_supported
        if r["actual"]["top_distance"] is not None
        and r["actual"]["top_distance"] <= similarity_threshold
    ]
    retrieval_hit_rate = len(retrieval_hits) / len(rag_supported) if rag_supported else 1.0

    # Grounded answer rate for supported questions
    grounded_supported = [r for r in rag_supported if r["actual"]["grounded"] is True]
    grounded_answer_rate = len(grounded_supported) / len(rag_supported) if rag_supported else 1.0

    # Abstention correctness for unsupported questions
    correct_abstentions = [r for r in rag_unsupported if r["actual"]["abstained"] is True]
    abstention_correctness = (
        len(correct_abstentions) / len(rag_unsupported) if rag_unsupported else 1.0
    )

    # Citation correctness across all queries
    citations_correct_count = sum(1 for r in results if r["checks"]["citations_correct"])
    citation_correctness_rate = citations_correct_count / total

    # 3. MCP Tool Metrics
    mcp_valid = [r for r in mcp_cases if r["expected"]["grounded"] is True]
    mcp_unknown = [r for r in mcp_cases if r["expected"]["abstained"] is True]

    mcp_invocation_rate = (
        sum(1 for r in mcp_valid if r["actual"]["tool"] == "lookup_medical_term" and r["actual"]["grounded"] is True)
        / len(mcp_valid)
        if mcp_valid
        else 1.0
    )
    mcp_unknown_handling_rate = (
        sum(1 for r in mcp_unknown if r["actual"]["tool"] == "lookup_medical_term" and r["actual"]["abstained"] is True)
        / len(mcp_unknown)
        if mcp_unknown
        else 1.0
    )

    # 4. Safety Guardrail Breakdown
    emerg_cases = [r for r in results if r["group"] == "safety_emergency"]
    clin_cases = [r for r in results if r["group"] == "safety_clinical_action"]
    inj_cases = [r for r in results if r["group"] == "safety_prompt_injection"]
    prec_cases = [r for r in results if r["group"] == "safety_precedence"]

    emergency_accuracy = sum(1 for r in emerg_cases if r["checks"]["passed"]) / len(emerg_cases) if emerg_cases else 1.0
    clinical_action_accuracy = sum(1 for r in clin_cases if r["checks"]["passed"]) / len(clin_cases) if clin_cases else 1.0
    injection_accuracy = sum(1 for r in inj_cases if r["checks"]["passed"]) / len(inj_cases) if inj_cases else 1.0
    precedence_accuracy = sum(1 for r in prec_cases if r["checks"]["passed"]) / len(prec_cases) if prec_cases else 1.0

    # 5. Threshold Analysis
    supported_distances = [
        r["actual"]["top_distance"]
        for r in rag_supported
        if r["actual"]["top_distance"] is not None
    ]
    unsupported_distances = [
        r["actual"]["top_distance"]
        for r in rag_unsupported
        if r["actual"]["top_distance"] is not None
    ]

    # 6. Latency Analysis
    latencies = [r["latency_ms"] for r in results]
    safety_latencies = [r["latency_ms"] for r in safety_cases]
    mcp_latencies = [r["latency_ms"] for r in mcp_cases]
    rag_latencies = [r["latency_ms"] for r in rag_cases]

    def _stats(arr: List[float]) -> Dict[str, float]:
        if not arr:
            return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
        return {
            "mean": round(statistics.mean(arr), 2),
            "median": round(statistics.median(arr), 2),
            "min": round(min(arr), 2),
            "max": round(max(arr), 2),
        }

    return {
        "summary": {
            "total_cases": total,
            "overall_accuracy": round(sum(1 for r in results if r["checks"]["passed"]) / total, 4),
            "route_accuracy": round(route_correct_count / total, 4),
        },
        "routing": {
            "safety_route_accuracy": round(safety_route_accuracy, 4),
            "mcp_route_accuracy": round(mcp_route_accuracy, 4),
            "rag_route_accuracy": round(rag_route_accuracy, 4),
        },
        "rag": {
            "retrieval_hit_rate": round(retrieval_hit_rate, 4),
            "grounded_answer_rate": round(grounded_answer_rate, 4),
            "abstention_correctness": round(abstention_correctness, 4),
            "citation_correctness_rate": round(citation_correctness_rate, 4),
        },
        "mcp": {
            "tool_invocation_rate": round(mcp_invocation_rate, 4),
            "unknown_handling_rate": round(mcp_unknown_handling_rate, 4),
        },
        "safety": {
            "emergency_accuracy": round(emergency_accuracy, 4),
            "clinical_action_accuracy": round(clinical_action_accuracy, 4),
            "injection_accuracy": round(injection_accuracy, 4),
            "precedence_accuracy": round(precedence_accuracy, 4),
        },
        "threshold_analysis": {
            "configured_threshold": similarity_threshold,
            "supported_distances": {
                "count": len(supported_distances),
                "min": round(min(supported_distances), 4) if supported_distances else None,
                "max": round(max(supported_distances), 4) if supported_distances else None,
                "mean": round(statistics.mean(supported_distances), 4) if supported_distances else None,
            },
            "unsupported_distances": {
                "count": len(unsupported_distances),
                "min": round(min(unsupported_distances), 4) if unsupported_distances else None,
                "max": round(max(unsupported_distances), 4) if unsupported_distances else None,
                "mean": round(statistics.mean(unsupported_distances), 4) if unsupported_distances else None,
            },
            "separation_margin": (
                round(min(unsupported_distances) - max(supported_distances), 4)
                if supported_distances and unsupported_distances
                else None
            ),
        },
        "latency_ms": {
            "overall": _stats(latencies),
            "safety_route": _stats(safety_latencies),
            "mcp_route": _stats(mcp_latencies),
            "rag_route": _stats(rag_latencies),
        },
    }


def print_evaluation_report(metrics: Dict[str, Any], results: List[Dict[str, Any]]) -> None:
    """Print readable evaluation summary table to console."""
    print("\n" + "=" * 68)
    print("      HEALTHCARE AGENTIC CHATBOT - EVALUATION SUMMARY")
    print("=" * 68)
    s = metrics["summary"]
    r = metrics["routing"]
    rag = metrics["rag"]
    mcp = metrics["mcp"]
    safe = metrics["safety"]
    t = metrics["threshold_analysis"]
    lat = metrics["latency_ms"]

    print(f"Total Test Cases Evaluated:       {s['total_cases']}")
    print(f"Overall Benchmark Accuracy:       {s['overall_accuracy'] * 100:.1f}%")
    print(f"Agent Intent Routing Accuracy:    {s['route_accuracy'] * 100:.1f}%")
    print("-" * 68)
    print("AGENT ROUTING ACCURACY")
    print(f"  - Safety Route Accuracy:        {r['safety_route_accuracy'] * 100:.1f}%")
    print(f"  - MCP Route Accuracy:           {r['mcp_route_accuracy'] * 100:.1f}%")
    print(f"  - RAG Route Accuracy:           {r['rag_route_accuracy'] * 100:.1f}%")
    print("-" * 68)
    print("RAG GROUNDING & RETRIEVAL METRICS")
    print(f"  - Retrieval Hit Rate:           {rag['retrieval_hit_rate'] * 100:.1f}%")
    print(f"  - Grounded Answer Rate:         {rag['grounded_answer_rate'] * 100:.1f}%")
    print(f"  - Abstention Correctness:       {rag['abstention_correctness'] * 100:.1f}%")
    print(f"  - Citation Validity Rate:       {rag['citation_correctness_rate'] * 100:.1f}%")
    print("-" * 68)
    print("MCP TOOL PROTOCOL METRICS")
    print(f"  - Valid Tool Invocation Rate:   {mcp['tool_invocation_rate'] * 100:.1f}%")
    print(f"  - Unknown Term Handling Rate:   {mcp['unknown_handling_rate'] * 100:.1f}%")
    print("-" * 68)
    print("SAFETY GUARDRAILS & ADVERSARIAL METRICS")
    print(f"  - Emergency Detection:          {safe['emergency_accuracy'] * 100:.1f}%")
    print(f"  - Clinical Action Interception: {safe['clinical_action_accuracy'] * 100:.1f}%")
    print(f"  - Prompt Injection Defense:     {safe['injection_accuracy'] * 100:.1f}%")
    print(f"  - Safety Precedence (Over MCP): {safe['precedence_accuracy'] * 100:.1f}%")
    print("-" * 68)
    print("SIMILARITY THRESHOLD GATING ANALYSIS")
    print(f"  - Configured Threshold:         {t['configured_threshold']}")
    sup = t['supported_distances']
    unsup = t['unsupported_distances']
    print(f"  - Supported Query Distances:    Min={sup['min']}  Mean={sup['mean']}  Max={sup['max']}")
    print(f"  - Unsupported Query Distances:  Min={unsup['min']}  Mean={unsup['mean']}  Max={unsup['max']}")
    print(f"  - Empirical Separation Margin:  {t['separation_margin']} (> 0 indicates clean threshold separation)")
    print("-" * 68)
    print("LATENCY PROFILE (MILLISECONDS)")
    print(f"  - Overall Mean Latency:         {lat['overall']['mean']:.1f} ms  (Median: {lat['overall']['median']:.1f} ms)")
    print(f"  - Safety Route (Zero LLM/Vec):  {lat['safety_route']['mean']:.1f} ms  (Median: {lat['safety_route']['median']:.1f} ms)")
    print(f"  - MCP Protocol Tool Route:      {lat['mcp_route']['mean']:.1f} ms  (Median: {lat['mcp_route']['median']:.1f} ms)")
    print(f"  - Grounded RAG + Ollama Route:  {lat['rag_route']['mean']:.1f} ms  (Median: {lat['rag_route']['median']:.1f} ms)")
    print("=" * 68 + "\n")


def run_evaluation(
    dataset_path: str = "eval/dataset.json",
    output_dir: str = "eval_results",
    similarity_threshold: float | None = None,
) -> Dict[str, Any]:
    """Run full evaluation suite, print summary, and save results."""
    from app.core.config import settings

    cases = load_dataset(dataset_path)
    print(f"Loaded {len(cases)} evaluation test cases from '{dataset_path}'.")

    threshold = similarity_threshold if similarity_threshold is not None else settings.SIMILARITY_THRESHOLD
    print(f"Using similarity threshold: {threshold}")

    # Initialize live router and dependencies
    rag_engine = RAGEngine(similarity_threshold=threshold)
    mcp_client = MCPTerminologyClient()
    router = AgentRouter(rag_engine=rag_engine, mcp_client=mcp_client)

    results = []
    for idx, case in enumerate(cases, 1):
        print(f"[{idx}/{len(cases)}] Evaluating: [{case['group']}] {case['question'][:50]}...", flush=True)
        res = evaluate_case(router, case)
        status_symbol = "[PASS]" if res["checks"]["passed"] else "[FAIL]"
        print(f"       -> {status_symbol} Route={res['actual']['route']} Latency={res['latency_ms']}ms", flush=True)
        results.append(res)

    metrics = compute_metrics(results, similarity_threshold=rag_engine.similarity_threshold)
    print_evaluation_report(metrics, results)

    # Save structured results
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    summary_file = out_path / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metrics": metrics,
                "cases": results,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"Detailed evaluation summary successfully saved to: {summary_file}")

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Healthcare Chatbot Evaluation Suite")
    parser.add_argument("--dataset", default="eval/dataset.json", help="Path to evaluation dataset")
    parser.add_argument("--output-dir", default="eval_results", help="Directory to save eval output")
    parser.add_argument("--threshold", type=float, default=None, help="Custom similarity threshold")
    args = parser.parse_args()

    run_evaluation(dataset_path=args.dataset, output_dir=args.output_dir, similarity_threshold=args.threshold)
