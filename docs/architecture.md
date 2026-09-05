# Healthcare Agentic RAG Chatbot - System Architecture

## Overview
This document outlines the multi-layer architecture of the Healthcare Agentic RAG Chatbot, designed for local privacy-preserving healthcare information retrieval.

## System Topology
```
┌──────────────────────────────────────────────────────────┐
│               React Frontend (Vite)                      │
│  - Modern Chat Dashboard, Citations Accordion, Disclaimers│
└────────────────────────────┬─────────────────────────────┘
                             │ HTTP REST / JSON
                             ▼
┌──────────────────────────────────────────────────────────┐
│                   FastAPI Backend API                    │
│  - Routes: /health, /health/ollama, /chat, /ingest       │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│               Agentic Orchestration Layer                │
│  - Intent Classification & Tool Routing                  │
│  - Evidence Validator & Safety Refusal Gate              │
└──────────────┬────────────────────────────┬──────────────┘
               │                            │
               ▼                            ▼
┌────────────────────────────┐  ┌──────────────────────────┐
│      RAG Subsystem         │  │     MCP Tool Subsystem   │
│ - PyMuPDF Page Parser      │  │ - Terminology Lookup     │
│ - BGE-Small Embeddings     │  │ - Medical Acronym Tool   │
│ - Persistent ChromaDB      │  │ - Official MCP SDK v2    │
└──────────────┬─────────────┘  └──────────────────────────┘
               │
               ▼
┌────────────────────────────┐
│      Local Ollama LLM      │
│         qwen3:8b           │
└────────────────────────────┘
```

## Layer Descriptions
1. **API Layer (`app/api`)**: Handles web requests, validation, CORS, and request logging.
2. **Agentic Layer (`app/agents`)**: Evaluates user queries, decides tool routing, validates evidence quality, and manages refusal/abstention logic.
3. **RAG Subsystem (`app/rag`)**: Page-aware PDF text extraction, metadata-rich recursive chunking, `bge-small-en-v1.5` embeddings, and ChromaDB vector persistence.
4. **MCP Subsystem (`app/mcp`)**: Standardized Model Context Protocol server exposing deterministic healthcare terminology lookup tools.
5. **LLM Engine (`app/llm`)**: Low-latency HTTP client abstraction communicating with local Ollama (`qwen3:8b`).
