from fastapi import FastAPI

from app.api.routes.customers import router as customers_router
from app.api.routes.tags import router as tags_router
from app.db.database import init_db


app = FastAPI(
    title="Customer Details CRUD API",
    description="Database-backed REST API for customers, addresses, business profiles, and tags.",
    version="1.0.0",
)

app.include_router(customers_router)
app.include_router(tags_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
