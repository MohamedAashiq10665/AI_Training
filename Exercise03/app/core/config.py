import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openweather_api_key: str | None
    jsonplaceholder_bearer_token: str | None
    external_timeout_seconds: float
    external_max_retries: int
    external_backoff_seconds: float

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            openweather_api_key=os.getenv("OPENWEATHER_API_KEY"),
            jsonplaceholder_bearer_token=os.getenv("JSONPLACEHOLDER_BEARER_TOKEN"),
            external_timeout_seconds=float(os.getenv("EXTERNAL_TIMEOUT_SECONDS", "5.0")),
            external_max_retries=int(os.getenv("EXTERNAL_MAX_RETRIES", "2")),
            external_backoff_seconds=float(os.getenv("EXTERNAL_BACKOFF_SECONDS", "0.25")),
        )
