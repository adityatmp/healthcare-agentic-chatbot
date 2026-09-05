# Retrieval-Augmented Generation (RAG) System Design

## Overview
The RAG subsystem processes healthcare PDFs into structured, searchable vector embeddings, preserving page-level origin for source citations and enforcing a strict similarity threshold gate to prevent hallucinations.

## Pipeline Architecture
```
Healthcare PDF (data/documents/*.pdf)
   │
   ▼
PyMuPDF Page Parser (backend/app/rag/loader.py)
   │
   ▼
Metadata Preserving Chunker (backend/app/rag/splitter.py)
   │  - Configurable CHUNK_SIZE=500, CHUNK_OVERLAP=50
   │  - Attaches: chunk_id (e.g. cdc_hypertension_guide_p2_c0), source, page
   ▼
Local BGE Embeddings (backend/app/rag/embeddings.py)
   │  - BAAI/bge-small-en-v1.5 (384-dimensional dense vectors)
   ▼
Persistent ChromaDB Vector Store (backend/app/rag/vector_store.py)
   │  - Metric: Cosine Distance (0.0 = identical, 1.0 = orthogonal)
   ▼
Relevance Distance Gate (backend/app/rag/engine.py)
   │  - Threshold: SIMILARITY_THRESHOLD=0.45
   │  - Distance <= 0.45 ──► Send to Ollama (qwen3:8b) ──► Grounded Response + Page Citations
   │  - Distance > 0.45  ──► Safe Abstention ("I don't have enough information...")
```

## CLI Usage Instructions

### Document Ingestion
```bash
python -m scripts.rag_cli ingest --docs-dir data/documents
```

### Grounded RAG Query
```bash
python -m scripts.rag_cli query "What are the recommended lifestyle modifications and DASH diet sodium limits for high blood pressure?"
```

## Verification & Distance Metric Calibration
- **Metric**: ChromaDB Cosine Distance (`hnsw:space: cosine`).
- **Relevant Query Distance**: `~0.103` (89.7% similarity match to CDC guidelines page 2).
- **Out-of-Scope Query Distance**: `~0.489` (exceeds default `0.45` threshold, triggering safe abstention).
