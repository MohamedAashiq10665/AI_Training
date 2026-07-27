from collections.abc import Sequence

import numpy as np

from app.core.config import Settings
from app.domain.models import ReviewDocument, SearchRequest, SearchResponse, SearchResult, SearchVariant
from app.services.dataset_loader import AppReviewDatasetLoader
from app.services.providers import (
    CrossEncoderReranker,
    EmbeddingProvider,
    OpenAIEmbeddingProvider,
    OpenSourceEmbeddingProvider,
    Reranker,
)


class SemanticSearchPipeline:
    def __init__(
        self,
        *,
        documents: Sequence[ReviewDocument],
        embedding_provider: EmbeddingProvider,
        reranker: Reranker | None = None,
        candidate_pool: int = 40,
    ) -> None:
        self.documents = list(documents)
        self.embedding_provider = embedding_provider
        self.reranker = reranker
        self.candidate_pool = max(candidate_pool, 1)
        self.embedding_matrix = self.embedding_provider.encode_texts(
            [document.search_text() for document in self.documents]
        )

    def search(self, query: str, top_k: int) -> list[SearchResult]:
        if not self.documents:
            return []

        query_vector = self.embedding_provider.encode_query(query)
        similarity_scores = np.matmul(self.embedding_matrix, query_vector)

        candidate_count = min(max(top_k, self.candidate_pool), len(self.documents))
        candidate_indices = np.argsort(-similarity_scores)[:candidate_count]
        candidate_documents = [self.documents[index] for index in candidate_indices]
        candidate_scores = [float(similarity_scores[index]) for index in candidate_indices]

        if self.reranker is None:
            return [
                SearchResult.from_document(document, score=score)
                for document, score in zip(candidate_documents[:top_k], candidate_scores[:top_k], strict=False)
            ]

        rerank_scores = self.reranker.score(query, candidate_documents)
        reranked = sorted(
            zip(candidate_documents, candidate_scores, rerank_scores, strict=False),
            key=lambda item: item[2],
            reverse=True,
        )
        return [
            SearchResult.from_document(document, score=score, rerank_score=rerank_score)
            for document, score, rerank_score in reranked[:top_k]
        ]


class SemanticSearchService:
    def __init__(self, *, settings: Settings, dataset_loader: AppReviewDatasetLoader) -> None:
        self.settings = settings
        self.dataset_loader = dataset_loader
        self._pipeline_cache: dict[tuple[SearchVariant, int], SemanticSearchPipeline] = {}

    def search(self, request: SearchRequest) -> SearchResponse:
        dataset_limit = request.dataset_limit or self.settings.default_dataset_limit
        pipeline = self.get_pipeline(variant=request.variant, dataset_limit=dataset_limit)
        results = pipeline.search(request.query, top_k=request.top_k or self.settings.default_top_k)
        return SearchResponse(
            variant=request.variant,
            query=request.query,
            total_indexed=len(pipeline.documents),
            results=results,
        )

    def get_pipeline(self, *, variant: SearchVariant, dataset_limit: int) -> SemanticSearchPipeline:
        cache_key = (variant, dataset_limit)
        if cache_key not in self._pipeline_cache:
            documents = self.dataset_loader.load_documents(dataset_limit)
            self._pipeline_cache[cache_key] = self.build_pipeline(variant=variant, documents=documents)
        return self._pipeline_cache[cache_key]

    def build_pipeline(
        self,
        *,
        variant: SearchVariant,
        documents: Sequence[ReviewDocument],
    ) -> SemanticSearchPipeline:
        embedding_provider = self._create_embedding_provider(variant)
        reranker = self._create_reranker(variant)
        return SemanticSearchPipeline(
            documents=documents,
            embedding_provider=embedding_provider,
            reranker=reranker,
            candidate_pool=self.settings.rerank_candidate_pool,
        )

    def _create_embedding_provider(self, variant: SearchVariant) -> EmbeddingProvider:
        if variant in {SearchVariant.OSS_NO_CROSS, SearchVariant.OSS_WITH_CROSS}:
            return OpenSourceEmbeddingProvider(self.settings.open_source_embedding_model)
        return OpenAIEmbeddingProvider(
            api_key=self.settings.openai_api_key or "",
            model_name=self.settings.openai_embedding_model,
        )

    def _create_reranker(self, variant: SearchVariant) -> Reranker | None:
        if variant in {SearchVariant.OSS_WITH_CROSS, SearchVariant.OPENAI_WITH_CROSS}:
            return CrossEncoderReranker(self.settings.cross_encoder_model)
        return None