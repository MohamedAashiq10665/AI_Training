from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "SSA FAQ RAG API"
    openai_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    answer_model: str = "gpt-4o-mini"
    ssa_faq_seed_url: str = "https://www.ssa.gov/faqs/en/questions/"
    index_path: Path = Path("data/ssa_faq_index.json")



def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        answer_model=os.getenv("ANSWER_MODEL", "gpt-4o-mini"),
        ssa_faq_seed_url=os.getenv("SSA_FAQ_SEED_URL", "https://www.ssa.gov/faqs/en/questions/"),
        index_path=Path(os.getenv("SSA_FAQ_INDEX_PATH", "data/ssa_faq_index.json")),
    )
