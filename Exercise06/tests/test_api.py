from __future__ import annotations


def test_train_endpoint(client) -> None:
    response = client.post(
        "/rag/train",
        json={"max_list_pages": 2, "max_question_pages": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ingested_documents"] == 2
    assert payload["index_path"].endswith("ssa_faq_index.json")


def test_query_endpoint_with_match(client) -> None:
    response = client.post(
        "/rag/query",
        json={"query": "How do I apply for retirement?", "top_k": 3, "min_similarity": 0.2},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] != "No Content"
    assert payload["url"].startswith("https://www.ssa.gov/faqs/en/questions/")
    assert payload["matching_percentage"] > 0
    assert len(payload["matches"]) == 1


def test_query_endpoint_no_content(client) -> None:
    response = client.post(
        "/rag/query",
        json={"query": "unknown", "top_k": 3, "min_similarity": 0.8},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "No Content"
    assert payload["url"] is None
    assert payload["matching_percentage"] == 0.0
    assert payload["matches"] == []
