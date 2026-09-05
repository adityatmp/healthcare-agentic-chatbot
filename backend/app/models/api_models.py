from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.rag_models import SourceMetadata, RetrievalInfo, IngestionSummary


class HealthResponse(BaseModel):
    """Schema for /health endpoint response."""

    status: str = Field(..., json_schema_extra={"example": "healthy"})
    service: str = Field(..., json_schema_extra={"example": "healthcare-agentic-chatbot"})
    version: str = Field(..., json_schema_extra={"example": "0.1.0"})


class OllamaHealthResponse(BaseModel):
    """Schema for /health/ollama endpoint response."""

    status: str = Field(..., json_schema_extra={"example": "healthy"})
    base_url: str = Field(..., json_schema_extra={"example": "http://localhost:11434"})
    model: str = Field(..., json_schema_extra={"example": "qwen3:8b"})
    available_models: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Schema for /chat endpoint request."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        json_schema_extra={"example": "What are the DASH diet sodium limits for hypertension?"},
    )


class ChatResponse(BaseModel):
    """Schema for /chat endpoint response, compatible with React UI."""

    answer: str
    grounded: bool
    abstained: bool
    sources: List[SourceMetadata]
    retrieval_info: RetrievalInfo


class IngestResponse(BaseModel):
    """Schema for /ingest endpoint response."""

    message: str
    summary: IngestionSummary
