from __future__ import annotations

from pydantic import BaseModel, Field


class TrainRequest(BaseModel):
    max_list_pages: int = Field(default=15, ge=1, le=100)
    max_question_pages: int = Field(default=500, ge=1, le=5000)


class TrainResponse(BaseModel):
    ingested_documents: int
    index_path: str


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)
    min_similarity: float = Field(default=0.35, ge=0.0, le=1.0)


class MatchResult(BaseModel):
    question: str
    answer: str
    url: str
    similarity: float
    matching_percentage: float


class QueryResponse(BaseModel):
    query: str
    answer: str
    url: str | None
    matching_percentage: float
    matches: list[MatchResult]
