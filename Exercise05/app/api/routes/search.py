from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.domain.models import ComparisonRequest, ComparisonResponse, SearchRequest, SearchResponse
from app.services.dataset_loader import AppReviewDatasetLoader
from app.services.evaluator import SearchEvaluator
from app.services.search_engine import SemanticSearchService


router = APIRouter(prefix="/search", tags=["semantic-search"])


def get_dataset_loader(settings: Settings = Depends(get_settings)) -> AppReviewDatasetLoader:
    return AppReviewDatasetLoader(dataset_id=settings.dataset_id, seed=settings.dataset_sample_seed)


def get_search_service(
    settings: Settings = Depends(get_settings),
    dataset_loader: AppReviewDatasetLoader = Depends(get_dataset_loader),
) -> SemanticSearchService:
    return SemanticSearchService(settings=settings, dataset_loader=dataset_loader)


def get_search_evaluator(
    settings: Settings = Depends(get_settings),
    dataset_loader: AppReviewDatasetLoader = Depends(get_dataset_loader),
) -> SearchEvaluator:
    return SearchEvaluator(settings=settings, dataset_loader=dataset_loader)


@router.post("/", response_model=SearchResponse)
def run_search(
    request: SearchRequest,
    search_service: SemanticSearchService = Depends(get_search_service),
) -> SearchResponse:
    try:
        return search_service.search(request)
    except (ImportError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/compare", response_model=ComparisonResponse)
def compare_variants(
    request: ComparisonRequest,
    evaluator: SearchEvaluator = Depends(get_search_evaluator),
) -> ComparisonResponse:
    try:
        return evaluator.compare(request)
    except (ImportError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc