from enum import Enum

from pydantic import BaseModel, Field


class SearchVariant(str, Enum):
    OSS_NO_CROSS = "oss_no_cross"
    OSS_WITH_CROSS = "oss_with_cross"
    OPENAI_NO_CROSS = "openai_no_cross"
    OPENAI_WITH_CROSS = "openai_with_cross"


def sentiment_from_star(star: int) -> str:
    if star <= 2:
        return "negative"
    if star == 3:
        return "neutral"
    return "positive"


class ReviewDocument(BaseModel):
    document_id: str
    package_name: str
    review: str
    date: str
    star: int
    sentiment: str

    @property
    def package_label(self) -> str:
        return self.package_name.rsplit(".", maxsplit=1)[-1].replace("_", " ")

    def search_text(self) -> str:
        return (
            f"Application {self.package_label}. "
            f"Sentiment {self.sentiment}. "
            f"Star rating {self.star}. "
            f"Review {self.review}"
        )


class SearchResult(ReviewDocument):
    score: float
    rerank_score: float | None = None

    @classmethod
    def from_document(
        cls,
        document: ReviewDocument,
        *,
        score: float,
        rerank_score: float | None = None,
    ) -> "SearchResult":
        return cls(**document.model_dump(), score=score, rerank_score=rerank_score)


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    variant: SearchVariant
    top_k: int = Field(default=5, ge=1, le=20)
    dataset_limit: int = Field(default=1200, ge=100, le=5000)


class SearchResponse(BaseModel):
    variant: SearchVariant
    query: str
    total_indexed: int
    results: list[SearchResult]


class ComparisonRequest(BaseModel):
    variants: list[SearchVariant] = Field(default_factory=lambda: list(SearchVariant))
    corpus_size: int = Field(default=1200, ge=3, le=5000)
    evaluation_size: int = Field(default=80, ge=1, le=400)
    top_k: int = Field(default=10, ge=1, le=20)


class VariantMetrics(BaseModel):
    variant: SearchVariant
    accuracy_at_1: float
    hit_rate_at_k: float
    mean_reciprocal_rank: float
    avg_relevance: float
    queries_evaluated: int


class ComparisonResponse(BaseModel):
    metrics: list[VariantMetrics]
    best_variant: SearchVariant | None
    notes: list[str]