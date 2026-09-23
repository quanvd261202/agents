from __future__ import annotations

from pydantic import SecretStr

from app.core.config import Settings
from app.retrieval.embeddings import EmbeddingProvider, build_embedding_provider
from app.retrieval.repository import InMemoryRetrievalRepository, RetrievalRepository
from app.retrieval.service import RetrievalBudget, RetrievalIndex, RetrievalService


def build_embeddings(settings: Settings) -> EmbeddingProvider:
    return build_embedding_provider(
        settings.embedding_provider,
        settings.embedding_model,
        settings.embedding_dimensions,
        settings.llm_base_url,
        _secret(settings.openai_api_key),
    )


def _secret(value: SecretStr | None) -> str | None:
    return value.get_secret_value() if value else None


async def build_retrieval_service(
    settings: Settings, repository: RetrievalRepository | None = None
) -> RetrievalService:
    embeddings = build_embeddings(settings)
    repo = repository or InMemoryRetrievalRepository()
    if await repo.count() == 0:
        await RetrievalIndex(embeddings, repo).rebuild()
    return RetrievalService(
        embeddings, repo, RetrievalBudget(max_tokens=settings.retrieval_budget_tokens)
    )
