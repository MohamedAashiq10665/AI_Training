# Exercise06 - SSA FAQ RAG with OpenAI

This project creates a Retrieval-Augmented Generation (RAG) API that is trained using the U.S. Social Security Administration FAQ pages under:

- https://www.ssa.gov/faqs/en/questions/

The API answers user questions by retrieving the closest FAQ content and generating a response with an OpenAI model.

## Expected Behavior

- Uses OpenAI embeddings to find the best matching SSA FAQ entries.
- Uses an OpenAI chat model to produce a concise answer from retrieved FAQ context.
- Returns source URL(s) where the answer came from.
- Returns a matching percentage for each result.
- Returns `No Content` when no result passes the similarity threshold.

## Project Structure

```text
Exercise06/
├── .env.example
├── app/
│   ├── api/routes/rag.py
│   ├── core/config.py
│   ├── domain/models.py
│   ├── services/
│   │   ├── openai_embedder.py
│   │   ├── rag_service.py
│   │   ├── ssa_faq_scraper.py
│   │   └── vector_store.py
│   └── main.py
├── data/
├── pytest.ini
├── requirements.txt
└── tests/
    ├── conftest.py
    └── test_api.py
```

## Setup

From `AI_Training/Exercise06`:

```bash
pip install -r requirements.txt
```

Set environment variables (example for PowerShell):

```powershell
$env:OPENAI_API_KEY="your_key_here"
$env:EMBEDDING_MODEL="text-embedding-3-small"
$env:ANSWER_MODEL="gpt-4o-mini"
```

Run API:

```bash
uvicorn app.main:app --reload
```

Swagger docs:

- http://127.0.0.1:8000/docs

## Train the RAG

```bash
curl -X POST "http://127.0.0.1:8000/rag/train" \
  -H "Content-Type: application/json" \
  -d '{
    "max_list_pages": 15,
    "max_question_pages": 500
  }'
```

Example response:

```json
{
  "ingested_documents": 312,
  "index_path": "data/ssa_faq_index.json"
}
```

## Query the RAG

```bash
curl -X POST "http://127.0.0.1:8000/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I apply for retirement benefits?",
    "top_k": 3,
    "min_similarity": 0.35
  }'
```

Example response with match:

```json
{
  "query": "How do I apply for retirement benefits?",
  "answer": "You can apply for retirement benefits online.",
  "url": "https://www.ssa.gov/faqs/en/questions/KA-01891.html",
  "matching_percentage": 89.4,
  "matches": [
    {
      "question": "How can I apply for retirement benefits?",
      "answer": "You can apply online for retirement benefits...",
      "url": "https://www.ssa.gov/faqs/en/questions/KA-01891.html",
      "similarity": 0.894,
      "matching_percentage": 89.4
    }
  ]
}
```

Example response with no match:

```json
{
  "query": "Question that does not match SSA FAQ",
  "answer": "No Content",
  "url": null,
  "matching_percentage": 0.0,
  "matches": []
}
```

## Notes

- First training run may take time due to web scraping and embedding generation.
- If the FAQ website structure changes, scraper extraction logic may need adjustment.
- Tune `min_similarity` to make matching stricter or looser.
