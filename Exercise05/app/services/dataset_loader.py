from functools import lru_cache

from app.domain.models import ReviewDocument, sentiment_from_star


def _normalize_review_text(review: str) -> str:
    return " ".join(review.split())


@lru_cache(maxsize=12)
def _load_sampled_documents(dataset_id: str, limit: int, seed: int) -> tuple[ReviewDocument, ...]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise ImportError(
            "The 'datasets' package is required. Install dependencies with 'pip install -r requirements.txt'."
        ) from exc

    dataset = load_dataset(dataset_id, split="train")
    if limit < len(dataset):
        dataset = dataset.shuffle(seed=seed).select(range(limit))

    documents: list[ReviewDocument] = []
    for index, row in enumerate(dataset):
        review = _normalize_review_text(row["review"])
        if not review:
            continue
        documents.append(
            ReviewDocument(
                document_id=f"{row['package_name']}::{index}",
                package_name=row["package_name"],
                review=review,
                date=row["date"],
                star=int(row["star"]),
                sentiment=sentiment_from_star(int(row["star"])),
            )
        )
    return tuple(documents)


class AppReviewDatasetLoader:
    def __init__(self, dataset_id: str, seed: int = 42) -> None:
        self.dataset_id = dataset_id
        self.seed = seed

    def load_documents(self, limit: int) -> list[ReviewDocument]:
        return list(_load_sampled_documents(self.dataset_id, limit, self.seed))

    def load_corpus_and_queries(
        self,
        *,
        corpus_size: int,
        evaluation_size: int,
    ) -> tuple[list[ReviewDocument], list[ReviewDocument]]:
        total = corpus_size + evaluation_size
        documents = self.load_documents(total)
        if len(documents) < total:
            raise ValueError(
                f"Requested {total} records but the dataset loader returned {len(documents)} records."
            )
        return documents[:corpus_size], documents[corpus_size:total]