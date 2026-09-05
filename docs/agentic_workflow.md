# Agentic Workflow & Routing Architecture

## Overview
The agent orchestration layer determines how incoming user queries are handled. Rather than a static RAG pipeline, the system dynamically routes queries based on intent and evidence.

## Decision Flow
```
User Query
   │
   ▼
Intent Classifier ───► Emergency / Clinical Claim Guard ───► Conservative Safety Response
   │
   ├──────► Medical Terminology Query ───► MCP Terminology Tool
   │
   └──────► General Healthcare Knowledge Query ───► RAG Retrieval
                                                       │
                                                       ▼
                                            Distance Score Check
                                            (Configurable SIMILARITY_THRESHOLD)
                                                       │
                                    ┌──────────────────┴──────────────────┐
                                    ▼                                     ▼
                             Score <= Threshold                     Score > Threshold
                                    │                                     │
                                    ▼                                     ▼
                             Ollama LLM (qwen3:8b)                  Safe Abstention Path
                             Grounded Response + Sources            "Insufficient evidence..."
```
