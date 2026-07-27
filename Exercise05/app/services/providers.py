from functools import lru_cache
from typing import Protocol, Sequence

import numpy as np

from app.domain.models import ReviewDocument


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class EmbeddingProvider(Protocol):
    def encode_texts(self, texts: Sequence[str]) -> np.ndarray:
        ...

    def encode_query(self, text: str) -> np.ndarray:
        ...


class Reranker(Protocol):
    def score(self, query: str, documents: Sequence[ReviewDocument]) -> list[float]:
        ...


@lru_cache(maxsize=4)
def _get_sentence_transformer(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "The 'sentence-transformers' package is required for open-source retrieval variants."
        ) from exc
    return SentenceTransformer(model_name)


@lru_cache(maxsize=2)
def _get_cross_encoder(model_name: str):
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise ImportError(
            "The 'sentence-transformers' package is required for cross-encoder reranking."
        ) from exc
    return CrossEncoder(model_name)


class OpenSourceEmbeddingProvider:
    def __init__(self, model_name: str) -> None:
        self.model = _get_sentence_transformer(model_name)

    def encode_texts(self, texts: Sequence[str]) -> np.ndarray:
        embeddings = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype=np.float32)

    def encode_query(self, text: str) -> np.ndarray:
        return self.encode_texts([text])[0]


class OpenAIEmbeddingProvider:
    def __init__(self, *, api_key: str, model_name: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI embedding variants.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("The 'openai' package is required for the OpenAI variants.") from exc

        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def encode_texts(self, texts: Sequence[str]) -> np.ndarray:
        response = self.client.embeddings.create(model=self.model_name, input=list(texts))
        vectors = np.asarray([item.embedding for item in response.data], dtype=np.float32)
        return _normalize_rows(vectors)

    def encode_query(self, text: str) -> np.ndarray:
        return self.encode_texts([text])[0]


class CrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        self.model = _get_cross_encoder(model_name)

    def score(self, query: str, documents: Sequence[ReviewDocument]) -> list[float]:
        pairs = [[query, document.search_text()] for document in documents]
        scores = self.model.predict(pairs)
        return [float(score) for score in scores]