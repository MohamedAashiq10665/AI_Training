from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    log_level: str = "INFO"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "resource_allocation"
    postgres_user: str = "resource_user"
    postgres_password: str = "resource_password"
    database_url: str | None = None

    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
