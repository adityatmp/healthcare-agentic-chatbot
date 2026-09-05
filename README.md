# Healthcare Agentic RAG Chatbot

An IIT Kanpur mentored production-grade AI portfolio project implementing a privacy-focused local Healthcare Information Assistant.

The system combines **Retrieval-Augmented Generation (RAG)**, **Agentic Orchestration**, **Model Context Protocol (MCP)** tools, local **Ollama** inference (`qwen3:8b`), page-aware source citations, and conservative healthcare safety guardrails.

---

## 🏛️ Architecture Overview

```
 USER QUERY ──► AGENTIC ORCHESTRATOR ──┬──► RAG RETRIEVAL (ChromaDB + PyMuPDF + BGE Embeddings)
                                      ├──► MCP TOOLS (Medical Terminology Server)
                                      └──► CONSERVATIVE SAFETY REFUSAL
                                              │
                                              ▼
                                    GROUNDED OLLAMA LLM (qwen3:8b)
                                              │
                                              ▼
                                    ANSWER WITH PAGE CITATIONS
```

---

## 🚀 Key Features

- **Grounded Document Retrieval**: Page-aware PDF parsing preserving filename, page number, and chunk metadata.
- **Local Privacy & Zero Cloud Dependency**: Embeddings (`BAAI/bge-small-en-v1.5`) and LLM inference (`qwen3:8b`) run 100% locally on system hardware.
- **Agentic Decision Engine**: Intent router and evidence validator to abstain when knowledge base lacks supporting evidence.
- **MCP Tool Protocol**: Standalone Model Context Protocol tool server for offline medical terminology resolution (`mcp>=2.0.0`).
- **Conservative Healthcare Guardrails**: Non-diagnostic emergency advice, refusal of prescription changes, and prompt injection defense.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, PyMuPDF, ChromaDB, Sentence-Transformers, MCP Python SDK v2, Pytest
- **LLM Engine**: Ollama (`qwen3:8b`)
- **Frontend**: React, Vite
- **Storage**: Persistent ChromaDB Vector Database

---

## 📦 Getting Started

### Environment Setup
1. Clone repository and ensure Python 3.12 is available:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```
2. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
3. Verify local Ollama is running with `qwen3:8b`:
   ```bash
   ollama list
   ```

### Running Tests
```bash
.\.venv\Scripts\python.exe -m pytest tests/
```

---

## 📄 License
MIT License - Created for Portfolio & IIT Kanpur Mentored AI Engineering Demonstration.
