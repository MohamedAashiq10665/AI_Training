from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth_routes import router as auth_router
from backend.api.routes import router
from backend.database.init_db import init_db
from backend.utils.exceptions import register_exception_handlers
from backend.utils.logging_config import configure_logging

configure_logging()

app = FastAPI(
    title="AI Resource Allocation & Bench Management",
    version="1.0.0",
    description="RAG-powered staffing recommendations and workforce analytics",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(router)
app.include_router(auth_router)


@app.on_event("startup")
def startup_init() -> None:
    init_db(seed=True)


@app.get("/")
def health() -> dict:
    return {"status": "ok", "service": "resource-allocation-rag"}
