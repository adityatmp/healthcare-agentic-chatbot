# Retrieval-Augmented Generation (RAG) System Design

## Overview
The RAG subsystem processes healthcare PDFs into structured, searchable vector embeddings, preserving page-level origin for source citations.

## Pipeline Breakdown
1. **Extraction**: `pymupdf` (fitz) extracts text page-by-page, attaching `{source_filename, page_number}`.
2. **Chunking**: `RecursiveCharacterTextSplitter` generates overlapping chunks with metadata preservation (`chunk_id`, `source_filename`, `page_number`).
3. **Embeddings**: Local `BAAI/bge-small-en-v1.5` transformer model generates 384-dimensional dense vectors.
4. **Vector Store**: `chromadb` persists collections locally in `data/processed/chroma`.
5. **Retrieval**: Similarity distance query returns Top-K nearest chunks alongside distance scores and source metadata.
6. **Grounding**: Distance threshold evaluation verifies whether retrieved context is sufficiently relevant to prompt the LLM.
