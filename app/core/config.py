from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="UIB_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://uib:uib@localhost:5432/uib"
    # Where lessons, run stages and graph checkpoints live. `postgres` uses `database_url` and
    # falls back to `memory` with a warning when the database does not answer.
    persistence: Literal["postgres", "memory"] = "postgres"

    # LLM. Leave `llm_model` empty to take the provider's default from app.core.llm.DEFAULT_MODELS.
    llm_provider: Literal["openai", "anthropic", "fake"] = "openai"
    llm_model: str = ""
    llm_base_url: str | None = None
    # The verifier reads screenshots. Empty uses `llm_model`. With OpenAI, gpt-4o counts image
    # tiles ~30x lighter than gpt-4o-mini, so it is cheaper and far kinder to rate limits.
    verifier_model: str = ""
    # Standard, unprefixed names, read from the environment or .env. Unset falls back to whatever
    # the SDK finds in the process environment.
    openai_api_key: SecretStr | None = Field(None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: SecretStr | None = Field(None, validation_alias="ANTHROPIC_API_KEY")

    # Photographs for image slots. `pexels` needs PEXELS_API_KEY (free); `fake` returns
    # deterministic test URLs; `none` keeps the art-directed placeholders.
    image_provider: Literal["pexels", "fake", "none"] = "pexels"
    pexels_api_key: SecretStr | None = Field(None, validation_alias="PEXELS_API_KEY")

    # Embeddings for retrieval. `hashing` is deterministic and offline, for tests and local runs.
    embedding_provider: Literal["openai", "hashing"] = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    max_design_iterations: int = 3
    # Screens built at once. Each verifier call sends three screenshots, which is heavy on
    # tokens-per-minute limits, so keep this low on small rate-limit tiers.
    max_parallel_screens: int = 2
    max_clarifier_questions: int = 3
    retrieval_budget_tokens: int = 1500
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
