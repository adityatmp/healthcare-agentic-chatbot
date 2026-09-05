from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile
from app.models.api_models import IngestResponse
from app.services.ingest_service import IngestService, get_ingest_service

router = APIRouter(tags=["Ingestion"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest PDF Healthcare Documents",
    description="Uploads one or multiple PDF documents into data/documents and runs page-aware text extraction, chunking, and ChromaDB vector persistence.",
)
def ingest_endpoint(
    files: Optional[List[UploadFile]] = File(None),
    ingest_service: IngestService = Depends(get_ingest_service),
):
    return ingest_service.handle_ingest(files)
