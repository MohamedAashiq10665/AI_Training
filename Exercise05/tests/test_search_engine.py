from collections.abc import Sequence

import numpy as np

from app.core.config import Settings
from app.domain.models import ComparisonRequest, ReviewDocument, SearchVariant
from app.services.dataset_loader import AppReviewDatasetLoader
from app.services.evaluator import SearchEvaluator
from app.services.search_engine import SemanticSearchPipeline


class KeywordEmbeddingProvider:
    vocabulary = (
        "calendar",
        "sync",
        "bug",
        "crash",
        "mail",
        "design",
        "feature",
        "positive",
        "negative",
    )

    def encode_texts(self, texts: Sequence[str]) -> np.ndarray:
        rows = []
        for text in texts:
            lowered = text.lower()
            vector = np.asarray([float(lowered.count(token)) for token in self.vocabulary], dtype=np.float32)
            if not vector.any():
                vector[0] = 1.0
            vector = vector / np.linalg.norm(vector)
            rows.append(vector)
        return np.vstack(rows)

    def encode_query(self, text: str) -> np.ndarray:
        return self.encode_texts([text])[0]


class ExactPhraseReranker:
    def score(self, query: str, documents: Sequence[ReviewDocument]) -> list[float]:
        lowered_query = query.lower()
        scores = []
        for document in documents:
            score = 0.0
            if document.package_label in lowered_query:
                score += 3.0
            if document.sentiment in lowered_query:
                score += 2.0
            if any(word in document.review.lower() for word in lowered_query.split()):
                score += 1.0
            scores.append(score)
        return scores


class StubDatasetLoader(AppReviewDatasetLoader):
    def __init__(self, corpus: list[ReviewDocument], queries: list[ReviewDocument]) -> None:
        self.corpus = corpus
        self.queries = queries

    def load_corpus_and_queries(
        self,
        *,
        corpus_size: int,
        evaluation_size: int,
    ) -> tuple[list[ReviewDocument], list[ReviewDocument]]:
        return self.corpus[:corpus_size], self.queries[:evaluation_size]


def make_documents() -> list[ReviewDocument]:
    return [
        ReviewDocument(
            document_id="calendar-1",
            package_name="org.fdroid.calendar",
            review="Calendar sync bug makes events disappear.",
            date="2026-01-01",
            star=1,
            sentiment="negative",
        ),
        ReviewDocument(
            document_id="calendar-2",
            package_name="org.fdroid.calendar",
            review="Negative calendar sync issue after update.",
            date="2026-01-02",
            star=2,
            sentiment="negative",
        ),
        ReviewDocument(
            document_id="mail-1",
            package_name="org.fdroid.mail",
            review="Mail design is positive and easy to use.",
            date="2026-01-03",
            star=5,
            sentiment="positive",
        ),
    ]


def test_pipeline_returns_ranked_documents() -> None:
    documents = make_documents()
    pipeline = SemanticSearchPipeline(
        documents=documents,
        embedding_provider=KeywordEmbeddingProvider(),
        candidate_pool=3,
    )

    results = pipeline.search("negative calendar sync bug", top_k=2)

    assert len(results) == 2
    assert results[0].package_name == "org.fdroid.calendar"
    assert results[0].score >= results[1].score


def test_reranker_adds_rerank_score() -> None:
    documents = make_documents()
    pipeline = SemanticSearchPipeline(
        documents=documents,
        embedding_provider=KeywordEmbeddingProvider(),
        reranker=ExactPhraseReranker(),
        candidate_pool=3,
    )

    results = pipeline.search("negative feedback for calendar", top_k=2)

    assert results[0].rerank_score is not None
    assert results[0].package_name == "org.fdroid.calendar"


def test_evaluator_reports_metrics_for_multiple_variants() -> None:
    corpus = make_documents()
    queries = [
        ReviewDocument(
            document_id="calendar-q",
            package_name="org.fdroid.calendar",
            review="Calendar sync is still broken after update.",
            date="2026-01-04",
            star=1,
            sentiment="negative",
        ),
        ReviewDocument(
            document_id="mail-q",
            package_name="org.fdroid.mail",
            review="Positive mail design and simple usage.",
            date="2026-01-05",
            star=5,
            sentiment="positive",
        ),
    ]

    settings = Settings(
        dataset_id="stub",
        open_source_embedding_model="stub",
        cross_encoder_model="stub",
        openai_embedding_model="stub",
        openai_api_key=None,
        default_dataset_limit=10,
        default_top_k=5,
        rerank_candidate_pool=3,
        dataset_sample_seed=42,
    )

    loader = StubDatasetLoader(corpus=corpus, queries=queries)

    def pipeline_factory(variant: SearchVariant, documents: Sequence[ReviewDocument]) -> SemanticSearchPipeline:
        reranker = ExactPhraseReranker() if variant in {SearchVariant.OSS_WITH_CROSS} else None
        return SemanticSearchPipeline(
            documents=documents,
            embedding_provider=KeywordEmbeddingProvider(),
            reranker=reranker,
            candidate_pool=3,
        )

    evaluator = SearchEvaluator(settings=settings, dataset_loader=loader, pipeline_factory=pipeline_factory)
    response = evaluator.compare(
        ComparisonRequest(
            variants=[SearchVariant.OSS_NO_CROSS, SearchVariant.OSS_WITH_CROSS],
            corpus_size=3,
            evaluation_size=2,
            top_k=2,
        )
    )

    assert len(response.metrics) == 2
    assert response.best_variant in {SearchVariant.OSS_NO_CROSS, SearchVariant.OSS_WITH_CROSS}
    assert all(metric.queries_evaluated == 2 for metric in response.metrics)