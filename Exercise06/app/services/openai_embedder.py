from __future__ import annotations

from openai import OpenAI


class OpenAIEmbedder:
    def __init__(self, api_key: str, embedding_model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._embedding_model = embedding_model

    def embed_text(self, text: str) -> list[float]:
        response = self._client.embeddings.create(
            model=self._embedding_model,
            input=[text],
        )
        return response.data[0].embedding

    def embed_texts(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self._client.embeddings.create(
                model=self._embedding_model,
                input=batch,
            )
            embeddings.extend([item.embedding for item in response.data])
        return embeddings
