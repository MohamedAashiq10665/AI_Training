from __future__ import annotations

from rag.embeddings.embedding_generator import EmbeddingGenerator
from rag.ingestion.chunking import chunk_text
from rag.ingestion.document_loader import (
    build_employee_documents_from_records,
    load_employee_documents,
)
from rag.ingestion.text_cleaner import clean_text
from rag.retrieval.ranking_engine import rerank
from rag.retrieval.retriever import search
from rag.vector_store.faiss_manager import FAISSManager


class EmployeeRAGPipeline:
    def __init__(self, employee_csv_path: str = "data/employees.csv"):
        self.employee_csv_path = employee_csv_path
        self.embedder = EmbeddingGenerator()
        self.faiss = FAISSManager()

    def build_index(self) -> None:
        documents = load_employee_documents(self.employee_csv_path)
        chunks = []
        for doc in documents:
            cleaned = clean_text(doc["text"])
            text_chunks = chunk_text(cleaned)
            for chunk in text_chunks:
                chunks.append({"text": chunk, "metadata": doc["metadata"]})

        vectors = self.embedder.encode([c["text"] for c in chunks])
        self.faiss.build_index(vectors, chunks)

    def build_index_from_records(self, employee_records: list[dict]) -> None:
        documents = build_employee_documents_from_records(employee_records)
        chunks = []
        for doc in documents:
            cleaned = clean_text(doc["text"])
            text_chunks = chunk_text(cleaned)
            for chunk in text_chunks:
                chunks.append({"text": chunk, "metadata": doc["metadata"]})

        vectors = self.embedder.encode([c["text"] for c in chunks])
        self.faiss.build_index(vectors, chunks)

    def retrieve_candidates(self, query: str, top_k: int = 10, availability_only: bool = True):
        if not self.faiss.index_path.exists() or not self.faiss.metadata_path.exists():
            self.build_index()

        index, metadata = self.faiss.load()
        query_vector = self.embedder.encode([clean_text(query)])[0]
        results = search(index, query_vector, metadata, top_k=top_k)
        return rerank(results, availability_only=availability_only)


if __name__ == "__main__":
    pipeline = EmployeeRAGPipeline()
    pipeline.build_index()
    print("FAISS index built: data/employees.index")
