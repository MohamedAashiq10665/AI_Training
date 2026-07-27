from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
import pytest

from app.api.routes.rag import get_rag_service
from app.main import app


class FakeRAGService:
    def train(self, max_list_pages: int, max_question_pages: int) -> int:
        return 2

    def answer_query(self, query: str, top_k: int, min_similarity: float) -> dict[str, Any]:
        if query.lower() == "unknown":
            return {
                "query": query,
                "answer": "No Content",
                "url": None,
                "matching_percentage": 0.0,
                "matches": [],
            }

        return {
            "query": query,
            "answer": "You can apply online for retirement benefits.",
            "url": "https://www.ssa.gov/faqs/en/questions/KA-01891.html",
            "matching_percentage": 89.4,
            "matches": [
                {
                    "question": "How can I apply for retirement benefits?",
                    "answer": "You can apply online for retirement benefits.",
                    "url": "https://www.ssa.gov/faqs/en/questions/KA-01891.html",
                    "similarity": 0.894,
                    "matching_percentage": 89.4,
                }
            ],
        }


@pytest.fixture()
def client() -> TestClient:
    app.dependency_overrides[get_rag_service] = lambda: FakeRAGService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
