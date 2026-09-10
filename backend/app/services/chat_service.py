import logging

from app.agents.router import AgentRouter
from app.models.api_models import ChatRequest, ChatResponse

logger = logging.getLogger("healthcare_chatbot.services.chat")


class ChatService:
    """Service encapsulating agentic chat execution."""

    def __init__(self, agent_router: AgentRouter | None = None):
        self.agent_router = agent_router or AgentRouter()

    def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Processes a user question through the agentic workflow."""

        logger.info("Processing chat request: '%s'", request.question)

        result = self.agent_router.run(request.question)

        return ChatResponse(
            answer=result.answer,
            grounded=result.grounded,
            abstained=result.abstained,
            sources=result.sources,
            retrieval_info=result.retrieval_info,
            tool_used=result.tool_used,
        )


_chat_service_instance = None


def get_chat_service() -> ChatService:
    global _chat_service_instance

    if _chat_service_instance is None:
        _chat_service_instance = ChatService()

    return _chat_service_instance