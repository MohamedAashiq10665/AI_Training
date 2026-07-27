from fastapi import FastAPI

from app.api.routes.search import router as search_router


app = FastAPI(
    title="Exercise05 Semantic Search Benchmark",
    version="1.0.0",
    description=(
        "Semantic search and retrieval-quality comparison for the Hugging Face "
        "app review dataset using open-source and OpenAI embeddings."
    ),
)

app.include_router(search_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Semantic search benchmark is running.",
        "docs": "/docs",
        "compare_endpoint": "/search/compare",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}