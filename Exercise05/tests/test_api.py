from app.api.routes.search import get_search_evaluator, get_search_service
from app.domain.models import ComparisonResponse, SearchResponse, SearchVariant, VariantMetrics
from app.main import app


class FakeSearchService:
    def search(self, request):
        return SearchResponse(
            variant=request.variant,
            query=request.query,
            total_indexed=2,
            results=[],
        )


class FakeEvaluator:
    def compare(self, request):
        return ComparisonResponse(
            metrics=[
                VariantMetrics(
                    variant=SearchVariant.OSS_NO_CROSS,
                    accuracy_at_1=0.5,
                    hit_rate_at_k=0.8,
                    mean_reciprocal_rank=0.6,
                    avg_relevance=0.4,
                    queries_evaluated=request.evaluation_size,
                )
            ],
            best_variant=SearchVariant.OSS_NO_CROSS,
            notes=["stub"],
        )


def test_root_healthcheck(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_endpoint_returns_response(client) -> None:
    app.dependency_overrides[get_search_service] = lambda: FakeSearchService()
    try:
        response = client.post(
            "/search/",
            json={
                "query": "negative calendar sync bug",
                "variant": "oss_no_cross",
                "top_k": 5,
                "dataset_limit": 500,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["variant"] == "oss_no_cross"
    assert payload["total_indexed"] == 2


def test_compare_endpoint_returns_metrics(client) -> None:
    app.dependency_overrides[get_search_evaluator] = lambda: FakeEvaluator()
    try:
        response = client.post(
            "/search/compare",
            json={
                "corpus_size": 500,
                "evaluation_size": 40,
                "top_k": 10,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["best_variant"] == "oss_no_cross"
    assert payload["metrics"][0]["queries_evaluated"] == 40