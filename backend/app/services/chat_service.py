import logging
from app.rag.engine import RAGEngine
from app.models.api_models import ChatRequest, ChatResponse

logger = logging.getLogger("healthcare_chatbot.services.chat")


class ChatService:
    """Service encapsulating RAG chat query execution."""

    def __init__(self, rag_engine: RAGEngine = None):
        self.rag_engine = rag_engine or RAGEngine()

    def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Processes user question through the RAG engine.

        Args:
            request: ChatRequest object containing the question.

        Returns:
            ChatResponse object formatted for frontend UI consumption.
        """
        logger.info(f"Processing chat request: '{request.question}'")
        rag_res = self.rag_engine.query(request.question)

        return ChatResponse(
            answer=rag_res.answer,
            grounded=rag_res.grounded,
            abstained=rag_res.abstained,
            sources=rag_res.sources,
            retrieval_info=rag_res.retrieval_info,
        )


# Global singleton instance for injection
_chat_service_instance = None


def get_chat_service() -> ChatService:
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance
