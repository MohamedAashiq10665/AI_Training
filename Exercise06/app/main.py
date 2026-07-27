from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.rag import router as rag_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.include_router(rag_router)


@app.get("/")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
