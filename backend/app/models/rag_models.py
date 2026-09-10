from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentPage(BaseModel):
    """Represents a single page extracted from a PDF document."""

    content: str
    metadata: dict = Field(
        default_factory=dict,
        description="Metadata containing source filename, page number, total_pages.",
    )


class TextChunk(BaseModel):
    """Represents a split text chunk with preserved origin metadata."""

    chunk_id: str
    content: str
    source_filename: str
    page_number: int
    chunk_index: int


class SourceMetadata(BaseModel):
    """Metadata attached to a retrieved source citation."""

    document: str
    page: int
    chunk_id: str
    distance: float


class RetrievalInfo(BaseModel):
    """Retrieval execution metadata for debugging and observability."""

    used: bool
    results_count: int
    top_distance: Optional[float] = None
    threshold: float


class RAGResponse(BaseModel):
    """Structured response object for RAG queries."""

    answer: str
    grounded: bool
    abstained: bool
    sources: List[SourceMetadata]
    retrieval_info: RetrievalInfo
    tool_used: Optional[str] = None


class IngestionSummary(BaseModel):
    """Summary of document ingestion pipeline execution."""

    documents_processed: int
    pages_processed: int
    chunks_created: int
    chunks_stored: int
    errors: List[str] = Field(default_factory=list)
