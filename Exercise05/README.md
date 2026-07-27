# Exercise05 - Semantic Search Benchmark for App Reviews

This exercise builds a semantic search project on top of the Hugging Face dataset `sealuzh/app_reviews` and compares four retrieval variants:

- open-source embeddings without a cross-encoder reranker
- open-source embeddings with a cross-encoder reranker
- OpenAI embeddings without a cross-encoder reranker
- OpenAI embeddings with a cross-encoder reranker

The project exposes a FastAPI service that can:

- run ad hoc semantic search over a sampled subset of app reviews
- compare retrieval accuracy across the four variants
- explain the tradeoff between faster bi-encoder retrieval and slower reranked retrieval

## Evaluation Design

The source dataset has these fields:

- `package_name`
- `review`
- `date`
- `star`

The dataset does not ship with query-relevance labels, so this exercise uses a weakly supervised evaluation setup:

1. A corpus split and an evaluation split are sampled from the dataset.
2. Each evaluation row is converted into a natural-language query.
3. A retrieved result is treated as relevant when it matches both:
   - the same `package_name`
   - the same sentiment bucket derived from the `star` value

Reported metrics:

- `accuracy_at_1`: the first result is relevant
- `hit_rate_at_k`: at least one of the top-k results is relevant
- `mean_reciprocal_rank`: ranking quality across the result list
- `avg_relevance`: fraction of top-k results that are relevant

This makes the benchmark reproducible and grounded in the real dataset while keeping the setup small enough for local experimentation.

## Project Structure

```text
Exercise05/
├── .env.example
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── search.py
│   ├── core/
│   │   └── config.py
│   ├── domain/
│   │   └── models.py
│   ├── services/
│   │   ├── dataset_loader.py
│   │   ├── evaluator.py
│   │   ├── providers.py
│   │   └── search_engine.py
│   └── main.py
├── pytest.ini
├── requirements.txt
└── tests/
    ├── conftest.py
    ├── test_api.py
    └── test_search_engine.py
```

## Setup

From `AI_Training/Exercise05`:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Docs URL:

- `http://127.0.0.1:8000/docs`

Optional environment variables:

- `OPENAI_API_KEY` for the OpenAI variants
- `APP_REVIEW_DATASET_ID` defaults to `sealuzh/app_reviews`
- `DEFAULT_DATASET_LIMIT` defaults to `1200`
- `DEFAULT_TOP_K` defaults to `5`
- `RERANK_CANDIDATE_POOL` defaults to `40`

## Example Requests

Run a search with open-source embeddings and cross-encoder reranking:

```bash
curl -X POST "http://127.0.0.1:8000/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "negative reviews about calendar sync problems",
    "variant": "oss_with_cross",
    "top_k": 5,
    "dataset_limit": 1000
  }'
```

Compare variants:

```bash
curl -X POST "http://127.0.0.1:8000/search/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "corpus_size": 1200,
    "evaluation_size": 80,
    "top_k": 10
  }'
```

## Notes

- The first request for a model-backed variant will be slower because the embedding model or cross-encoder has to load.
- The OpenAI variants require `OPENAI_API_KEY` and internet access.
- The reranked variants should usually improve ranking quality, but they cost additional latency.