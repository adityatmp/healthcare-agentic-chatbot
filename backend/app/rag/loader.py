import json
import os
import logging
from typing import List, Optional, Dict, Any
import pymupdf
from app.models.rag_models import DocumentPage

logger = logging.getLogger("healthcare_chatbot.rag.loader")


class PDFLoader:
    """Page-aware PDF document text extractor using PyMuPDF."""

    @staticmethod
    def _load_metadata_registry(file_path: str) -> Dict[str, Any]:
        """Attempts to find and load metadata.json for the document."""
        dir_path = os.path.dirname(file_path)
        candidates = [
            os.path.join(dir_path, "metadata.json"),
            os.path.join(dir_path, "..", "metadata.json"),
        ]
        for candidate in candidates:
            norm_candidate = os.path.normpath(candidate)
            if os.path.exists(norm_candidate):
                try:
                    with open(norm_candidate, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning("Failed reading metadata registry at '%s': %s", norm_candidate, e)
        return {}

    @classmethod
    def load_pdf(
        cls, file_path: str, doc_metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentPage]:
        """Extracts text page-by-page from a PDF file preserving page metadata.

        Args:
            file_path: Absolute or relative path to the PDF file.
            doc_metadata: Optional metadata dictionary with title, organization, url.

        Returns:
            List of DocumentPage objects containing page content and metadata.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at path: {file_path}")

        filename = os.path.basename(file_path)
        pages: List[DocumentPage] = []

        # Resolve document metadata
        if doc_metadata is None:
            registry = cls._load_metadata_registry(file_path)
            doc_metadata = registry.get(filename, {})

        org = doc_metadata.get("organization")
        url = doc_metadata.get("url")
        title = doc_metadata.get("title", filename)

        try:
            doc = pymupdf.open(file_path)
            total_pages = len(doc)
            logger.info("Opening PDF '%s' (%d pages)", filename, total_pages)

            for page_num in range(1, total_pages + 1):
                page = doc.load_page(page_num - 1)
                text = page.get_text("text")

                # Clean whitespace
                cleaned_text = "\n".join(
                    [line.strip() for line in text.splitlines() if line.strip()]
                )

                if not cleaned_text:
                    logger.warning(
                        "Page %d in '%s' is empty or unreadable (possible scanned image).",
                        page_num,
                        filename,
                    )
                    continue

                page_doc = DocumentPage(
                    content=cleaned_text,
                    metadata={
                        "source": filename,
                        "page": page_num,
                        "total_pages": total_pages,
                        "organization": org,
                        "url": url,
                        "title": title,
                    },
                )
                pages.append(page_doc)

            logger.info(
                "Successfully extracted %d readable pages from '%s'", len(pages), filename
            )
            doc.close()
            return pages

        except Exception as e:
            logger.error("Error extracting PDF '%s': %s", filename, str(e))
            raise e
