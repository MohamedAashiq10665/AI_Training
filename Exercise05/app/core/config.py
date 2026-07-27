from dataclasses import dataclass
from functools import lru_cache
import os


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return int(raw_value)


@dataclass(frozen=True)
class Settings:
    dataset_id: str
    open_source_embedding_model: str
    cross_encoder_model: str
    openai_embedding_model: str
    openai_api_key: str | None
    default_dataset_limit: int
    default_top_k: int
    rerank_candidate_pool: int
    dataset_sample_seed: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        dataset_id=os.getenv("APP_REVIEW_DATASET_ID", "sealuzh/app_reviews"),
        open_source_embedding_model=os.getenv(
            "OPEN_SOURCE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        cross_encoder_model=os.getenv(
            "CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
        ),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        default_dataset_limit=_int_env("DEFAULT_DATASET_LIMIT", 1200),
        default_top_k=_int_env("DEFAULT_TOP_K", 5),
        rerank_candidate_pool=_int_env("RERANK_CANDIDATE_POOL", 40),
        dataset_sample_seed=_int_env("DATASET_SAMPLE_SEED", 42),
    )