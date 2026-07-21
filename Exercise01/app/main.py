from fastapi import FastAPI

from app.api.routes.customers import router as customers_router
from app.api.routes.tags import router as tags_router


app = FastAPI(
    title="Customer Details CRUD API",
    description="Mock-data REST API for customers, addresses, business profiles, and tags.",
    version="1.0.0",
)

app.include_router(customers_router)
app.include_router(tags_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
