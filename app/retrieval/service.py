"""Retrieval + context budgeting. The catalog is never sent to the model in full."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.logging import get_logger
from app.models.direction import DesignDirection
from app.models.requirements import ClarifiedRequirements
from app.retrieval.embeddings import EmbeddingProvider
from app.retrieval.indexer import build_documents
from app.retrieval.models import (
    RetrievalDocument,
    RetrievalFilters,
    RetrievalHit,
    RetrievalKind,
    RetrievedContext,
)
from app.retrieval.repository import RetrievalRepository

log = get_logger(__name__)

#: Rough characters-per-token used only to keep the context inside its budget.
_CHARS_PER_TOKEN = 4


def estimate_tokens(lines: list[str]) -> int:
    return sum(len(line) // _CHARS_PER_TOKEN + 1 for line in lines)


@dataclass(frozen=True)
class RetrievalBudget:
    """Caps on what reaches the LLM, per kind and overall."""

    max_components: int = 14
    max_layouts: int = 6
    max_recipes: int = 3
    max_lessons: int = 5
    max_tokens: int = 1500


class RetrievalIndex:
    """Embeds the registries once and writes them to the repository."""

    def __init__(self, embeddings: EmbeddingProvider, repository: RetrievalRepository) -> None:
        self._embeddings = embeddings
        self._repository = repository

    async def rebuild(self, documents: list[RetrievalDocument] | None = None) -> int:
        docs = documents if documents is not None else build_documents()
        vectors = await self._embeddings.embed_documents([d.text for d in docs])
        await self._repository.upsert(docs, vectors)
        log.info("retrieval.indexed", count=len(docs), embedder=self._embeddings.name)
        return len(docs)


class RetrievalService:
    """Satisfies app.services.interfaces.RetrievalService."""

    def __init__(
        self,
        embeddings: EmbeddingProvider,
        repository: RetrievalRepository,
        budget: RetrievalBudget | None = None,
    ) -> None:
        self._embeddings = embeddings
        self._repository = repository
        self._budget = budget or RetrievalBudget()

    async def search(
        self, query: str, filters: RetrievalFilters | None = None, limit: int = 10
    ) -> list[RetrievalHit]:
        vector = await self._embeddings.embed_query(query)
        return await self._repository.search(vector, filters or RetrievalFilters(), limit)

    @staticmethod
    def build_query(req: ClarifiedRequirements, direction: DesignDirection) -> str:
        return " ".join(
            filter(
                None,
                [
                    direction.visual_style.replace("_", " "),
                    direction.layout_strategy.replace("_", " "),
                    req.domain,
                    req.product,
                    req.primary_goal,
                    " ".join(req.key_features),
                    direction.recipe.replace("_", " "),
                ],
            )
        )

    async def retrieve(
        self,
        req: ClarifiedRequirements,
        direction: DesignDirection,
        lessons: list[str] | None = None,
    ) -> RetrievedContext:
        query = self.build_query(req, direction)
        style = direction.visual_style.split("_")[-1] or None

        components = await self.search(
            query,
            RetrievalFilters(kinds=[RetrievalKind.component], domain=req.domain, style=style),
            self._budget.max_components,
        )
        if not components:  # style is a soft signal; never let it empty the catalog
            components = await self.search(
                query,
                RetrievalFilters(kinds=[RetrievalKind.component], domain=req.domain),
                self._budget.max_components,
            )
        layouts = await self.search(
            query, RetrievalFilters(kinds=[RetrievalKind.layout]), self._budget.max_layouts
        )
        recipes = await self.search(
            query,
            RetrievalFilters(kinds=[RetrievalKind.recipe], domain=req.domain),
            self._budget.max_recipes,
        )

        context = RetrievedContext(
            components=[h.document.summary for h in components],
            layouts=[h.document.summary for h in layouts],
            recipes=[h.document.summary for h in recipes],
            lessons=(lessons or [])[: self._budget.max_lessons],
        )
        return self._apply_budget(context)

    def _apply_budget(self, ctx: RetrievedContext) -> RetrievedContext:
        """Trim least-relevant entries until the whole context fits. Recipes are kept first
        because the Design Builder cannot produce a valid spec without one."""
        order = ["lessons", "layouts", "components"]
        while True:
            total = estimate_tokens(ctx.components + ctx.layouts + ctx.recipes + ctx.lessons)
            if total <= self._budget.max_tokens:
                ctx.estimated_tokens = total
                return ctx
            for field in order:
                values: list[str] = getattr(ctx, field)
                if len(values) > 1:
                    values.pop()
                    break
            else:
                ctx.estimated_tokens = total
                return ctx
