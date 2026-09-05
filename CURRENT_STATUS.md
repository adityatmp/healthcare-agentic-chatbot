# Project Current Status - Healthcare Agentic RAG Chatbot

## Current Milestone
- **Milestone 1: Core RAG Vertical Slice** — [COMPLETED]

## Completed Milestones
- [x] **Milestone 0: Project Foundations & Structure**
- [x] **Milestone 1: Core RAG Vertical Slice**

## Milestone 1 Deliverables & Technical Specs
- **PDF Extraction**: Page-aware loader (`backend/app/rag/loader.py`) using `pymupdf` preserving filename, page number, and skipping unreadable pages.
- **Metadata Preserving Chunking**: `MetadataPreservingSplitter` (`backend/app/rag/splitter.py`) with configurable `chunk_size=500` and `chunk_overlap=50`.
- **Local Embeddings**: `LocalEmbeddingService` (`backend/app/rag/embeddings.py`) using `BAAI/bge-small-en-v1.5` (384-dim dense vectors).
- **Persistent Vector Store**: `VectorStoreManager` (`backend/app/rag/vector_store.py`) using persistent ChromaDB with explicit Cosine distance space (`hnsw:space: cosine`).
- **Ollama Client**: `OllamaClient` (`backend/app/llm/ollama_client.py`) using `/api/chat` endpoint targeting `qwen3:8b`.
- **RAG Engine & Grounding Gate**: `RAGEngine` (`backend/app/rag/engine.py`) enforcing configurable Cosine distance similarity threshold (`SIMILARITY_THRESHOLD=0.45`), prompt injection XML encapsulation (`<context>`), and safe refusal on weak evidence.
- **CLI Workflow**: `scripts/rag_cli.py` (`ingest` and `query` subcommands).
- **Sample Document**: `data/documents/cdc_hypertension_guide.pdf` (3 pages of CDC clinical guidelines).

## Test Results
- `6 passed` in Pytest test suite (`tests/test_health.py`, `tests/test_rag.py`).
- Real query test passed with `qwen3:8b` grounded answer and page citations (`[1] cdc_hypertension_guide.pdf | Page: 2 | Distance: 0.1032`).
- Real out-of-scope query test verified abstention path (`Top Distance: 0.4889 > 0.45 threshold`).

## Next Milestone
- **Milestone 2: FastAPI Backend Layer** (Awaiting user approval)
