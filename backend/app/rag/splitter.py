import logging
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.rag_models import DocumentPage, TextChunk

logger = logging.getLogger("healthcare_chatbot.rag.splitter")


class MetadataPreservingSplitter:
    """Recursive text splitter that preserves document source, page numbers, and chunk IDs."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split_pages(self, pages: List[DocumentPage]) -> List[TextChunk]:
        """Splits document pages into text chunks with rich metadata.

        Args:
            pages: List of DocumentPage objects.

        Returns:
            List of TextChunk objects.
        """
        chunks: List[TextChunk] = []

        for page in pages:
            source = page.metadata.get("source", "unknown.pdf")
            page_num = page.metadata.get("page", 1)

            split_texts = self._splitter.split_text(page.content)

            for idx, text in enumerate(split_texts):
                # Clean chunk ID format: document_p1_c0
                clean_source_stem = (
                    source.replace(".pdf", "")
                    .replace(" ", "_")
                    .replace("-", "_")
                    .lower()
                )
                chunk_id = f"{clean_source_stem}_p{page_num}_c{idx}"

                chunk = TextChunk(
                    chunk_id=chunk_id,
                    content=text,
                    source_filename=source,
                    page_number=page_num,
                    chunk_index=idx,
                )
                chunks.append(chunk)

        logger.info(
            f"Split {len(pages)} pages into {len(chunks)} chunks (size={self.chunk_size}, overlap={self.chunk_overlap})"
        )
        return chunks
