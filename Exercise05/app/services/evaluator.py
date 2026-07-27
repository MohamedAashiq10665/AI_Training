from collections.abc import Callable, Sequence

from app.core.config import Settings
from app.domain.models import ComparisonRequest, ComparisonResponse, ReviewDocument, SearchVariant, VariantMetrics
from app.services.dataset_loader import AppReviewDatasetLoader
from app.services.search_engine import SemanticSearchPipeline, SemanticSearchService


def _reciprocal_rank(matches: list[bool]) -> float:
    for index, is_match in enumerate(matches, start=1):
        if is_match:
            return 1.0 / index
    return 0.0


def build_query_from_document(document: ReviewDocument) -> str:
    review_excerpt = " ".join(document.review.split()[:18])
    return (
        f"{document.sentiment} feedback for the app {document.package_label}. "
        f"User comment: {review_excerpt}"
    )


def is_relevant(query_document: ReviewDocument, candidate: ReviewDocument) -> bool:
    return (
        query_document.package_name == candidate.package_name
        and query_document.sentiment == candidate.sentiment
    )


class SearchEvaluator:
    def __init__(
        self,
        *,
        settings: Settings,
        dataset_loader: AppReviewDatasetLoader,
        pipeline_factory: Callable[[SearchVariant, Sequence[ReviewDocument]], SemanticSearchPipeline] | None = None,
    ) -> None:
        self.settings = settings
        self.dataset_loader = dataset_loader
        if pipeline_factory is None:
            search_service = SemanticSearchService(settings=settings, dataset_loader=dataset_loader)
            self.pipeline_factory = lambda variant, documents: search_service.build_pipeline(
                variant=variant,
                documents=documents,
            )
        else:
            self.pipeline_factory = pipeline_factory

    def compare(self, request: ComparisonRequest) -> ComparisonResponse:
        corpus, evaluation_documents = self.dataset_loader.load_corpus_and_queries(
            corpus_size=request.corpus_size,
            evaluation_size=request.evaluation_size,
        )

        metrics = [self._evaluate_variant(variant, corpus, evaluation_documents, request.top_k) for variant in request.variants]
        best_variant = None
        if metrics:
            best_variant = max(
                metrics,
                key=lambda item: (item.hit_rate_at_k, item.accuracy_at_1, item.mean_reciprocal_rank),
            ).variant

        notes = [
            "Relevance uses package_name plus a sentiment bucket derived from the star rating.",
            "Cross-encoder variants rerank the best embedding matches, which usually improves ranking quality at higher latency.",
        ]
        if any(variant in {SearchVariant.OPENAI_NO_CROSS, SearchVariant.OPENAI_WITH_CROSS} for variant in request.variants):
            notes.append("OpenAI variants require OPENAI_API_KEY and internet access.")

        return ComparisonResponse(metrics=metrics, best_variant=best_variant, notes=notes)

    def _evaluate_variant(
        self,
        variant: SearchVariant,
        corpus: Sequence[ReviewDocument],
        evaluation_documents: Sequence[ReviewDocument],
        top_k: int,
    ) -> VariantMetrics:
        pipeline = self.pipeline_factory(variant, corpus)

        accuracy_at_1_hits = 0
        hit_rate_at_k_hits = 0
        reciprocal_rank_total = 0.0
        avg_relevance_total = 0.0

        for query_document in evaluation_documents:
            query = build_query_from_document(query_document)
            results = pipeline.search(query, top_k=top_k)
            matches = [is_relevant(query_document, result) for result in results]

            if matches and matches[0]:
                accuracy_at_1_hits += 1
            if any(matches):
                hit_rate_at_k_hits += 1

            reciprocal_rank_total += _reciprocal_rank(matches)
            avg_relevance_total += sum(matches) / max(len(matches), 1)

        evaluated_queries = len(evaluation_documents)
        return VariantMetrics(
            variant=variant,
            accuracy_at_1=accuracy_at_1_hits / evaluated_queries,
            hit_rate_at_k=hit_rate_at_k_hits / evaluated_queries,
            mean_reciprocal_rank=reciprocal_rank_total / evaluated_queries,
            avg_relevance=avg_relevance_total / evaluated_queries,
            queries_evaluated=evaluated_queries,
        )