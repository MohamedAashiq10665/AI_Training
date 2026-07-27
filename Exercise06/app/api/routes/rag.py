from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.domain.models import QueryRequest, QueryResponse, TrainRequest, TrainResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG"])



def get_rag_service() -> RAGService:
    settings = get_settings()
    try:
        return RAGService(settings)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/train", response_model=TrainResponse)
def train_rag(payload: TrainRequest, service: RAGService = Depends(get_rag_service)) -> TrainResponse:
    ingested = service.train(
        max_list_pages=payload.max_list_pages,
        max_question_pages=payload.max_question_pages,
    )
    settings = get_settings()
    return TrainResponse(ingested_documents=ingested, index_path=str(settings.index_path))


@router.post("/query", response_model=QueryResponse)
def query_rag(payload: QueryRequest, service: RAGService = Depends(get_rag_service)) -> QueryResponse:
    return service.answer_query(
        query=payload.query,
        top_k=payload.top_k,
        min_similarity=payload.min_similarity,
    )
