# Healthcare Agentic Chatbot

A local healthcare assistant prototype that answers medical questions using document retrieval, a Model Context Protocol (MCP) terminology tool, and heuristic safety guardrails. Everything runs locally on your machine with Ollama, so patient queries and documents never leave your local environment.

## What it does

- **Grounded Q&A via RAG**: Ingests curated source-derived healthcare reference summaries (distilled from CDC, NIH Office of Dietary Supplements, WHO, USDA, and MedlinePlus guidelines) using PyMuPDF, chunks them with page awareness, and stores them in ChromaDB with local BGE embeddings. When answering, it pulls relevant chunks and attaches page-level citations.
- **Abstention on low confidence**: Checks vector distance against a calibrated threshold (0.30). If retrieved chunks exceed this distance, it refuses to guess and informs the user that the knowledge base lacks sufficient evidence.
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
       ├───► Direct Greeting ───► Standard assistant welcome (no LLM/RAG/MCP)
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

1. **Python 3.12+**
2. **Node.js 18+**
3. **Ollama** installed with the `qwen3:8b` model pulled:
   ```bash
   ollama pull qwen3:8b
   ```

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/adityasharma/healthcare-agentic-chatbot.git
cd healthcare-agentic-chatbot

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# Ingest curated reference documents into ChromaDB
python scripts/ingest.py

# Run the FastAPI server
uvicorn app.main:app --app-dir backend --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## Evaluation

The project includes an evaluation runner (`python -m scripts.evaluate`) that tests 43 curated cases across 7 capability groups: supported RAG, unsupported RAG, MCP terminology, emergency safety, clinical action safety, prompt injection, and safety precedence.

Measured results with threshold 0.30 on local hardware (NVIDIA RTX 3050 Laptop GPU, with CPU/RAM offloading for `qwen3:8b`):

- **Routing accuracy**: 100.0% (43/43)
- **RAG retrieval hit rate**: 100.0% (14/14 on supported documents)
- **Grounded answer rate**: 78.6% (11/14 supported questions fully grounded; 3 abstained by LLM)
- **Vector abstention**: 100.0% (8/8 on unsupported questions)
- **Citation correctness**: 100.0% (43/43)
- **Safety guardrail accuracy**: 100.0% (16/16 across emergencies, clinical questions, and prompt injections)
- **MCP tool invocation rate**: 100.0% (4/4 valid terms, 1/1 clean abstention on unknown terms)
- **Average latency**: ~0.5 ms for safety, ~36 ms for MCP lookups, ~53 s median for grounded RAG generation with local Ollama

See `docs/evaluation.md` for the full breakdown and distance analysis.

## Repository Structure

```
healthcare-agentic-chatbot/
├── backend/
│   ├── app/
│   │   ├── agents/         # Intent router and safety precedence logic
│   │   ├── api/            # FastAPI routes (/chat, /health, /ingest)
│   │   ├── core/           # Configuration and threshold settings
│   │   ├── llm/            # Ollama client and prompt templates
│   │   ├── mcp/            # FastMCP terminology server and protocol client
│   │   ├── models/         # Pydantic request, response, and RAG schemas
│   │   ├── rag/            # Embeddings, Chroma vector store, and generation engine
│   │   └── services/       # Chat orchestration layer
│   └── requirements.txt
├── frontend/
│   ├── src/                # React chat UI and components
│   └── package.json
├── data/
│   ├── documents/          # 12 curated source-derived reference PDFs and provenance metadata
│   ├── raw/                # Original source PDFs
│   └── processed/chroma/   # Local Chroma vector database
├── eval/
│   └── dataset.json        # 43 test cases across 7 capability groups
├── scripts/
│   ├── evaluate.py         # Reproducible evaluation runner
│   ├── generate_corpus_pdfs.py # Clean reference PDF generator from authoritative sources
│   └── ingest.py           # Document ingestion script
├── tests/                  # 80 unit and integration tests
└── docs/                   # Architecture, RAG, safety, and evaluation notes
```

## Limitations

- **Prototype only**: Built for educational and portfolio demonstration purposes. It is not approved for clinical use.
- **Not medical advice**: The chatbot cannot diagnose conditions or prescribe medications. It is designed to refer users to doctors or emergency services when needed.
- **Curated reference summaries**: The RAG corpus consists of curated educational summaries distilled from official public health guidelines (CDC, NIH ODS, WHO, USDA, MedlinePlus) with exact metric and intake preservation, rather than direct agency publication PDFs.
- **Rule-based routing**: Intent classification and safety filters rely on deterministic regular expressions and keyword checks rather than a fine-tuned clinical classification model.
- **Small evaluation set**: The benchmark covers 43 specific test cases. It is an engineering sanity check, not a clinical trial.
- **Local inference speed**: Because it runs an 8B parameter model locally without cloud GPU infrastructure, generating grounded answers takes 30-80 seconds depending on local hardware.
