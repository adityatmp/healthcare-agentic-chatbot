import os
import logging
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from app.rag.engine import RAGEngine
from app.models.api_models import IngestResponse
from app.models.rag_models import IngestionSummary

logger = logging.getLogger("healthcare_chatbot.services.ingest")

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB limit per PDF
ALLOWED_EXTENSIONS = {".pdf"}


class IngestService:
    """Service handling PDF document upload validation and vector ingestion."""

    def __init__(
        self,
        rag_engine: RAGEngine = None,
        docs_dir: str = "data/documents",
    ):
        self.rag_engine = rag_engine or RAGEngine()
        self.docs_dir = docs_dir

    def handle_ingest(
        self, files: Optional[List[UploadFile]] = None
    ) -> IngestResponse:
        """Validates uploaded files, saves them safely, and executes vector store ingestion.

        Args:
            files: Optional list of FastAPI UploadFile objects.

        Returns:
            IngestResponse object containing message and summary.
        """
        os.makedirs(self.docs_dir, exist_ok=True)
        uploaded_filenames = []

        if files:
            for file in files:
                if not file.filename:
                    continue

                # Path traversal protection: extract basename strictly
                safe_filename = os.path.basename(file.filename)
                ext = os.path.splitext(safe_filename)[1].lower()

                if ext not in ALLOWED_EXTENSIONS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid file type '{ext}' for file '{safe_filename}'. Only PDF files (.pdf) are permitted.",
                    )

                # Check file size
                file.file.seek(0, os.SEEK_END)
                size = file.file.tell()
                file.file.seek(0)

                if size > MAX_FILE_SIZE_BYTES:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File '{safe_filename}' exceeds maximum allowed size of 20MB ({size} bytes).",
                    )

                dest_path = os.path.join(self.docs_dir, safe_filename)
                logger.info(f"Saving uploaded file '{safe_filename}' to '{dest_path}' ({size} bytes)")

                with open(dest_path, "wb") as f:
                    content = file.file.read()
                    f.write(content)

                uploaded_filenames.append(safe_filename)

        # Trigger RAG Engine directory ingestion
        summary = self.rag_engine.ingest_directory(self.docs_dir)

        msg = (
            f"Successfully processed upload of {len(uploaded_filenames)} file(s) and updated vector store."
            if uploaded_filenames
            else f"Re-processed documents in '{self.docs_dir}' directory."
        )

        return IngestResponse(message=msg, summary=summary)


# Global singleton instance for injection
_ingest_service_instance = None


def get_ingest_service() -> IngestService:
    global _ingest_service_instance
    if _ingest_service_instance is None:
        _ingest_service_instance = IngestService()
    return _ingest_service_instance
