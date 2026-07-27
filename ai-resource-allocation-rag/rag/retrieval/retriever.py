from __future__ import annotations

import numpy as np


def search(index, query_embedding, metadata: list[dict], top_k: int = 10) -> list[dict]:
    query_vector = np.array([query_embedding]).astype("float32")
    scores, indices = index.search(query_vector, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        results.append(
            {
                "score": float(score),
                "text": metadata[idx]["text"],
                "metadata": metadata[idx]["metadata"],
            }
        )
    return results
