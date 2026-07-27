from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np


class FAISSManager:
    def __init__(self, index_path: str = "data/employees.index", metadata_path: str = "data/employees_meta.json"):
        project_root = Path(__file__).resolve().parents[2]
        self.index_path = project_root / index_path
        self.metadata_path = project_root / metadata_path

    def build_index(self, embeddings: np.ndarray, metadata: list[dict]) -> None:
        vectors = np.array(embeddings).astype("float32")
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(self.index_path))
        self.metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    def load(self):
        index = faiss.read_index(str(self.index_path))
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return index, metadata
