from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="UIB_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://uib:uib@localhost:5432/uib"

    # LLM. Leave `llm_model` empty to take the provider's default from app.core.llm.DEFAULT_MODELS.
    llm_provider: Literal["openai", "anthropic", "fake"] = "openai"
    llm_model: str = ""
    llm_base_url: str | None = None

    # Embeddings for retrieval. `hashing` is deterministic and offline, for tests and local runs.
    embedding_provider: Literal["openai", "hashing"] = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    max_design_iterations: int = 3
    max_clarifier_questions: int = 3
    retrieval_budget_tokens: int = 1500
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
