from __future__ import annotations

import hashlib

import numpy as np


class EmbeddingGenerator:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.backend = "hash"
        self.model = None

        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name)
            self.backend = "sentence_transformers"
        except Exception:
            self.model = None

    def _hash_embed(self, text: str, dim: int = 384) -> np.ndarray:
        vec = np.zeros(dim, dtype="float32")
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            idx = int(digest[:8], 16) % dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def encode(self, texts: list[str]):
        if self.backend == "sentence_transformers" and self.model is not None:
            return self.model.encode(texts, normalize_embeddings=True)
        return np.array([self._hash_embed(text) for text in texts])
