"""Application configuration using Pydantic v2 BaseSettings."""
from __future__ import annotations

from typing import Literal
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://lenny:lennypass@localhost:5432/lennygrowth",
        description="Async SQLAlchemy database URL",
    )
    postgres_user: str = "lenny"
    postgres_password: str = "lennypass"
    postgres_db: str = "lennygrowth"

    # LLM Provider
    llm_provider: Literal["ollama", "anthropic", "openai"] = "ollama"
    model_name: str = "llama3.2"
    ollama_base_url: str = "http://host.docker.internal:11434"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    llm_timeout_seconds: int = 600

    # Retrieval
    retrieval_top_k: int = 8
    retrieval_min_score: float = 0.05

    # Router
    router_use_llm: bool = False

    # Ingest
    transcripts_repo_url: str = (
        "https://github.com/ChatPRD/lennys-podcast-transcripts"
    )
    ingest_max_episodes: int = 60
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 50

    # Logging
    log_level: str = "INFO"

    @computed_field  # type: ignore[misc]
    @property
    def has_cloud_fallback(self) -> bool:
        return bool(self.anthropic_api_key or self.openai_api_key)

    @computed_field  # type: ignore[misc]
    @property
    def fallback_provider(self) -> str | None:
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        return None


settings = Settings()
