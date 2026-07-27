from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from app.services.ssa_faq_scraper import FAQDocument


@dataclass(frozen=True)
class SearchResult:
    document: FAQDocument
    similarity: float

    @property
    def matching_percentage(self) -> float:
        return round(max(self.similarity, 0.0) * 100.0, 2)


class JSONVectorStore:
    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path

    def save(self, documents: list[FAQDocument], embeddings: list[list[float]]) -> None:
        payload = {
            "documents": [asdict(doc) for doc in documents],
            "embeddings": embeddings,
        }
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(payload), encoding="utf-8")

    def load(self) -> tuple[list[FAQDocument], np.ndarray]:
        if not self.index_path.exists():
            return [], np.array([])

        payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        documents = [FAQDocument(**doc) for doc in payload.get("documents", [])]
        embeddings = np.array(payload.get("embeddings", []), dtype=np.float32)
        return documents, embeddings

    def search(
        self,
        query_embedding: list[float],
        top_k: int,
        min_similarity: float,
    ) -> list[SearchResult]:
        documents, embeddings = self.load()
        if not documents or embeddings.size == 0:
            return []

        query = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            return []

        doc_norms = np.linalg.norm(embeddings, axis=1)
        denom = doc_norms * query_norm
        safe_denom = np.where(denom == 0, 1e-12, denom)
        cosine_scores = np.dot(embeddings, query) / safe_denom

        ranked_indices = np.argsort(cosine_scores)[::-1]
        results: list[SearchResult] = []

        for idx in ranked_indices:
            similarity = float(cosine_scores[idx])
            if similarity < min_similarity:
                continue
            results.append(SearchResult(document=documents[idx], similarity=similarity))
            if len(results) == top_k:
                break

        return results
