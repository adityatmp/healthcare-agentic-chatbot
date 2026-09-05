from fastapi import APIRouter, HTTPException
from app.models.api_models import HealthResponse, OllamaHealthResponse
from app.llm.ollama_client import OllamaClient, OllamaClientError
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application Health Check",
    description="Returns the overall operational status and version of the API service.",
)
def health_check():
    return HealthResponse(
        status="healthy",
        service="healthcare-agentic-chatbot",
        version="0.1.0",
    )


@router.get(
    "/health/ollama",
    response_model=OllamaHealthResponse,
    summary="Ollama LLM Engine Health Check",
    description="Verifies reachability of the local Ollama server and checks whether the configured model is available.",
)
def ollama_health_check():
    client = OllamaClient()
    try:
        health_info = client.check_health()
        return OllamaHealthResponse(
            status="healthy",
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            available_models=health_info.get("available_models", []),
        )
    except OllamaClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama health check failed: {str(e)}",
        )
