import logging
from typing import List
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger("healthcare_chatbot.rag.embeddings")


class LocalEmbeddingService:
    """Local text embedding service using SentenceTransformers."""

    _instance = None

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        self.model_name = model_name
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(
            f"Embedding model '{self.model_name}' loaded successfully (dimension={self.dimension})"
        )

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of text strings.

        Args:
            texts: List of text strings.

        Returns:
            List of float vector lists.
        """
        if not texts:
            return []
        embeddings = self.model.encode(
            texts, show_progress_bar=False, convert_to_numpy=True
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Generates embedding vector for a single query string.

        Args:
            query: Query text string.

        Returns:
            Embedding vector as list of floats.
        """
        embedding = self.model.encode(
            query, show_progress_bar=False, convert_to_numpy=True
        )
        return embedding.tolist()
