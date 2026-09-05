from fastapi import APIRouter, Depends, HTTPException
from app.models.api_models import ChatRequest, ChatResponse
from app.services.chat_service import ChatService, get_chat_service

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Grounded Healthcare Chat Query",
    description="Executes grounded RAG retrieval and returns LLM answer with source citations or safe abstention indicator.",
)
def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        return chat_service.process_chat(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing RAG chat query: {str(e)}",
        )
