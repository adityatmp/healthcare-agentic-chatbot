# Healthcare Agentic Chatbot

A local healthcare assistant prototype that answers medical questions using document retrieval, a Model Context Protocol (MCP) terminology tool, and heuristic safety guardrails. Everything runs locally on your machine with Ollama, so patient queries and documents never leave your local environment.

## What it does

- **Grounded Q&A via RAG**: Ingests clinical PDF guidelines (like CDC hypertension documentation) using PyMuPDF, chunks them, and stores them in ChromaDB with local BGE embeddings. When answering, it pulls relevant chunks and attaches page-level citations.
- **Abstention on low confidence**: Checks vector distance against a threshold (0.30). If the retrieved chunks aren't close enough, it refuses to guess and tells the user that the knowledge base doesn't have sufficient evidence.
- **MCP Terminology Lookups**: Includes an MCP server and client using the official MCP Python SDK for looking up medical definitions (e.g., hypertension, tachycardia) from a standardized terminology dataset.
- **Safety routing & guardrails**: Catches acute emergencies (chest pain, stroke signs, difficulty breathing), direct requests for diagnosis/prescriptions, and prompt injection attempts before invoking the model, routing users to immediate medical care or a physician.
- **Full-stack interface**: FastAPI backend exposing `/chat`, `/health`, and `/ingest` endpoints, paired with a React and Vite frontend that renders Markdown responses, source citations, route tags, and groundedness indicators.

## Architecture

```
React / Vite (Frontend)
       │
       ▼
FastAPI (/api/v1/chat)
       │
       ▼
ChatService
       │
       ▼
AgentRouter ───► Safety Guard ───► Emergency advice or doctor referral (no LLM)
       │
       ├───► MCP Client   ───► FastMCP Terminology Server (definition + source)
       │
       └───► RAG Engine   ───► ChromaDB Vector Search (BGE-small-en-v1.5)
                                    │
                         Distance <= 0.30?
                                    ├─► Yes: Ollama (qwen3:8b) ──► Grounded answer + citations
                                    └─► No:  Safe abstention (insufficient context)
```

## Tech Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic v2
- **RAG & Vector Search**: ChromaDB, Sentence-Transformers (`BAAI/bge-small-en-v1.5`), PyMuPDF (PDF chunking), LangChain text splitters
- **LLM**: Ollama running `qwen3:8b` locally
- **Tool Protocol**: Model Context Protocol (MCP Python SDK 2.x)
- **Frontend**: React 19, Vite, React-Markdown, Vanilla CSS
- **Testing & Tooling**: Pytest, Pytest-Asyncio, Oxlint

## Running Locally

### Prerequisites

- Python 3.12+
- Node.js 18+
- [Ollama](https://ollama.com/) installed

### 1. Set up Ollama and the model

Make sure Ollama is running and pull the model:

```bash
ollama serve
ollama pull qwen3:8b
```

### 2. Set up the backend

```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # On Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment variables
cp .env.example .env

# Run tests to make sure everything works
pytest
```

Start the backend server:

```powershell
$env:PYTHONPATH = "backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Set up the frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## Evaluation

The project includes an evaluation runner (`python -m scripts.evaluate`) that tests 29 curated cases across 7 capability groups: supported RAG, unsupported RAG, MCP terminology, emergency safety, clinical action safety, prompt injection, and safety precedence.

Measured results with threshold 0.30 on local hardware (NVIDIA RTX 3050 Laptop GPU, with CPU/RAM offloading for `qwen3:8b`):

- **Routing accuracy**: 100% (29/29)
- **RAG retrieval hit rate**: 100% (4/4 on supported documents)
- **Vector abstention**: 100% (4/4 on unsupported questions)
- **Citation correctness**: 100% (29/29)
- **Safety guardrail accuracy**: 100% (16/16 across emergencies, clinical questions, and prompt injections)
- **MCP tool invocation rate**: 100% (4/4 valid terms, 1/1 clean abstention on unknown terms)
- **Average latency**: ~0.1 ms for safety, ~11 ms for MCP lookups, ~33 s for grounded RAG generation with local Ollama

See `docs/evaluation.md` for the full breakdown and distance analysis.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── agents/         # Agent router, safety checks, and routing logic
│   │   ├── api/            # FastAPI route handlers (/chat, /health, /ingest)
│   │   ├── core/           # Configuration and settings
│   │   ├── mcp/            # FastMCP terminology server and protocol client
│   │   ├── models/         # Pydantic request, response, and RAG schemas
│   │   ├── rag/            # Embeddings, Chroma vector store, and generation engine
│   │   └── services/       # Chat orchestration layer
│   └── requirements.txt
├── frontend/
│   ├── src/                # React chat UI and components
│   └── package.json
├── data/
│   ├── raw/                # Source PDFs (CDC hypertension guidelines)
│   └── processed/chroma/   # Local Chroma vector database
├── eval/
│   └── dataset.json        # 29 test cases across 7 capability groups
├── scripts/
│   ├── evaluate.py         # Reproducible evaluation runner
│   └── ingest.py           # Document ingestion script
├── tests/                  # 78 unit and integration tests
└── docs/                   # Architecture, RAG, safety, and evaluation notes
```

## Limitations

- **Prototype only**: Built for educational and portfolio demonstration purposes. It is not approved for clinical use.
- **Not medical advice**: The chatbot cannot diagnose conditions or prescribe medications. It is designed to refer users to doctors or emergency services when needed.
- **Rule-based routing**: Intent classification and safety filters rely on deterministic regular expressions and keyword checks rather than a fine-tuned clinical classification model.
- **Small evaluation set**: The benchmark covers 29 specific test cases. It is an engineering sanity check, not a clinical trial.
- **Local inference speed**: Because it runs an 8B parameter model locally without cloud GPU infrastructure, generating grounded answers takes 30-70 seconds depending on local hardware.
