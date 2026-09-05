import time
import uuid
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.router import api_router
from app.llm.ollama_client import OllamaConnectionError, OllamaTimeoutError

# Logging Configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - [req_id=%(request_id)s] - %(message)s",
)


class RequestIdFilter(logging.Filter):
    """Logging filter to inject request_id into log records."""

    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "system"
        return True


logger = logging.getLogger("healthcare_chatbot.api")
logger.addFilter(RequestIdFilter())

app = FastAPI(
    title="Healthcare Agentic RAG Chatbot API",
    description=(
        "Production-grade local RAG chatbot API featuring page-aware PDF ingestion, "
        "persistent ChromaDB retrieval, Ollama local inference (qwen3:8b), "
        "and grounded source citations."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    """Middleware attaching X-Request-ID and logging request execution duration."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request.state.request_id = request_id

    start_time = time.time()
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra={"request_id": request_id},
    )

    try:
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = str(process_time)

        logger.info(
            f"Completed request: {request.method} {request.url.path} -> Status {response.status_code} ({process_time}ms)",
            extra={"request_id": request_id},
        )
        return response

    except Exception as exc:
        process_time = round((time.time() - start_time) * 1000, 2)
        logger.error(
            f"Unhandled exception during {request.method} {request.url.path}: {str(exc)} ({process_time}ms)",
            extra={"request_id": request_id},
        )
        raise exc


# Exception Handlers
@app.exception_handler(OllamaConnectionError)
async def ollama_connection_exception_handler(request: Request, exc: OllamaConnectionError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "Ollama Service Unavailable",
            "message": str(exc),
            "hint": "Ensure local Ollama service is running at http://localhost:11434",
        },
    )


@app.exception_handler(OllamaTimeoutError)
async def ollama_timeout_exception_handler(request: Request, exc: OllamaTimeoutError):
    return JSONResponse(
        status_code=504,
        content={
            "error": "Ollama Service Timeout",
            "message": str(exc),
            "hint": "The local LLM inference took too long. Try reducing prompt context size.",
        },
    )


# Mount API Router
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
