import os
import logging
from typing import List
import pymupdf
from app.models.rag_models import DocumentPage

logger = logging.getLogger("healthcare_chatbot.rag.loader")


class PDFLoader:
    """Page-aware PDF document text extractor using PyMuPDF."""

    @staticmethod
    def load_pdf(file_path: str) -> List[DocumentPage]:
        """Extracts text page-by-page from a PDF file preserving page metadata.

        Args:
            file_path: Absolute or relative path to the PDF file.

        Returns:
            List of DocumentPage objects containing page content and metadata.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at path: {file_path}")

        filename = os.path.basename(file_path)
        pages: List[DocumentPage] = []

        try:
            doc = pymupdf.open(file_path)
            total_pages = len(doc)
            logger.info(f"Opening PDF '{filename}' ({total_pages} pages)")

            for page_num in range(1, total_pages + 1):
                page = doc.load_page(page_num - 1)
                text = page.get_text("text")

                # Clean whitespace
                cleaned_text = "\n".join(
                    [line.strip() for line in text.splitlines() if line.strip()]
                )

                if not cleaned_text:
                    logger.warning(
                        f"Page {page_num} in '{filename}' is empty or unreadable (possible scanned image)."
                    )
                    continue

                page_doc = DocumentPage(
                    content=cleaned_text,
                    metadata={
                        "source": filename,
                        "page": page_num,
                        "total_pages": total_pages,
                    },
                )
                pages.append(page_doc)

            logger.info(
                f"Successfully extracted {len(pages)} readable pages from '{filename}'"
            )
            doc.close()
            return pages

        except Exception as e:
            logger.error(f"Error extracting PDF '{filename}': {str(e)}")
            raise e
