import os
import logging
from typing import List, Dict, Any
import chromadb
from app.core.config import settings
from app.models.rag_models import TextChunk

logger = logging.getLogger("healthcare_chatbot.rag.vector_store")


class VectorStoreManager:
    """Persistent local vector database manager using ChromaDB."""

    def __init__(
        self,
        db_path: str = settings.VECTOR_DB_PATH,
        collection_name: str = settings.COLLECTION_NAME,
    ):
        self.db_path = db_path
        self.collection_name = collection_name

        os.makedirs(self.db_path, exist_ok=True)
        logger.info(f"Initializing ChromaDB PersistentClient at '{self.db_path}'")

        self.client = chromadb.PersistentClient(path=self.db_path)
        # Explicitly configure cosine distance space (0.0 = identical, 1.0 = orthogonal)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaDB Collection '{self.collection_name}' ready (count={self.collection.count()})"
        )

    def add_chunks(
        self, chunks: List[TextChunk], embeddings: List[List[float]]
    ) -> int:
        """Stores or updates text chunks and their embeddings in ChromaDB.

        Args:
            chunks: List of TextChunk objects.
            embeddings: Corresponding list of embedding vectors.

        Returns:
            Number of chunks upserted.
        """
        if not chunks:
            return 0

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "source": chunk.source_filename,
                "page": chunk.page_number,
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(
            f"Upserted {len(chunks)} chunks into ChromaDB collection '{self.collection_name}'"
        )
        return len(chunks)

    def query(
        self, query_embedding: List[float], top_k: int = settings.TOP_K
    ) -> List[Dict[str, Any]]:
        """Queries the vector store for the top-K nearest matching text chunks.

        Args:
            query_embedding: Vector representation of user query.
            top_k: Number of nearest matches to retrieve.

        Returns:
            List of dictionary items containing id, document, metadata, and distance score.
        """
        if self.collection.count() == 0:
            logger.warning("Vector store collection is empty.")
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        matches = []
        if (
            results
            and "documents" in results
            and results["documents"]
            and results["documents"][0]
        ):
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for i in range(len(docs)):
                matches.append(
                    {
                        "id": ids[i],
                        "document": docs[i],
                        "metadata": metas[i],
                        "distance": float(distances[i]),
                    }
                )

        logger.info(
            f"Retrieved {len(matches)} matches from ChromaDB (top distance: {matches[0]['distance'] if matches else 'N/A'})"
        )
        return matches

    def count(self) -> int:
        """Returns total document count in the collection."""
        return self.collection.count()

    def clear(self) -> None:
        """Deletes all items from the collection."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Cleared collection '{self.collection_name}'")
