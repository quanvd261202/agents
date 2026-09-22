from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="UIB_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://uib:uib@localhost:5432/uib"
    llm_provider: Literal["anthropic", "fake"] = "anthropic"
    llm_model: str = "claude-sonnet-5"
    max_design_iterations: int = 3
    max_clarifier_questions: int = 3
    retrieval_budget_tokens: int = 1500
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
