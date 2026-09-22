"""pgvector repository against a real Postgres. Skipped when no database is reachable."""

from __future__ import annotations

import socket
from urllib.parse import urlparse

import pytest

from app.core.config import Settings
from app.retrieval import (
    HashingEmbeddingProvider,
    PgVectorRetrievalRepository,
    RetrievalFilters,
    RetrievalIndex,
    RetrievalKind,
    RetrievalService,
    build_documents,
)

pytest.importorskip("sqlalchemy")
pytest.importorskip("asyncpg")

DB_URL = Settings(_env_file=None).database_url
DIMS = 128


def _reachable(url: str) -> bool:
    parsed = urlparse(url.replace("postgresql+asyncpg", "postgresql"))
    try:
        with socket.create_connection((parsed.hostname or "localhost", parsed.port or 5432), 1.0):
            return True
    except OSError:
        return False


pytestmark = [
    pytest.mark.skipif(not _reachable(DB_URL), reason="no postgres reachable"),
    pytest.mark.integration,
]


@pytest.fixture
async def service():
    from app.db import build_session_factory, dispose_engine

    factory = build_session_factory(DB_URL)
    repo = PgVectorRetrievalRepository(factory, dimensions=DIMS)
    await repo.create_schema()
    embeddings = HashingEmbeddingProvider(dimensions=DIMS)
    await RetrievalIndex(embeddings, repo).rebuild()
    yield RetrievalService(embeddings, repo)
    await dispose_engine(DB_URL)


async def test_index_round_trips(service):
    assert await service._repository.count() == len(build_documents())


async def test_semantic_search(service):
    hits = await service.search(
        "premium saas analytics dashboard charts",
        RetrievalFilters(kinds=[RetrievalKind.component]),
        limit=8,
    )
    assert {h.document.id for h in hits} & {"stats", "chart_panel", "data_table"}
    assert all(0.0 <= h.score <= 1.0 for h in hits)


async def test_sql_filters_match_in_memory_semantics(service):
    saas = await service.search(
        "product grid", RetrievalFilters(kinds=[RetrievalKind.component], domain="saas"), limit=30
    )
    assert "product_card" not in {h.document.id for h in saas}

    trust = await service.search("trust", RetrievalFilters(any_capabilities=["trust"]), limit=30)
    assert {h.document.id for h in trust} >= {"social_proof", "trust_signals"}

    both = await service.search(
        "grid", RetrievalFilters(all_capabilities=["commerce", "responsive"]), limit=30
    )
    assert {h.document.id for h in both} <= {"product_card", "product_grid"}

    excluded = await service.search("hero", RetrievalFilters(exclude_ids=["hero"]), limit=10)
    assert "hero" not in {h.document.id for h in excluded}


async def test_upsert_is_idempotent(service):
    before = await service._repository.count()
    await RetrievalIndex(service._embeddings, service._repository).rebuild()
    assert await service._repository.count() == before


PARITY_CASES = [
    ("premium saas analytics dashboard charts", RetrievalFilters(kinds=[RetrievalKind.component])),
    ("running shoe store", RetrievalFilters(kinds=[RetrievalKind.component], domain="ecommerce")),
    ("product grid", RetrievalFilters(kinds=[RetrievalKind.component], domain="saas")),
    ("trust badges", RetrievalFilters(any_capabilities=["trust"])),
    ("responsive commerce grid", RetrievalFilters(all_capabilities=["commerce", "responsive"])),
    ("hero", RetrievalFilters(exclude_ids=["hero"])),
    ("card layout", RetrievalFilters(kinds=[RetrievalKind.layout])),
    ("premium page", RetrievalFilters(category="commerce")),
    ("editorial landing", RetrievalFilters(kinds=[RetrievalKind.recipe], domain="saas")),
    ("bento feature grid", RetrievalFilters(layout="bento")),
    ("premium hero", RetrievalFilters(style="premium")),
]


@pytest.fixture
async def in_memory_service():
    from app.retrieval import InMemoryRetrievalRepository

    embeddings = HashingEmbeddingProvider(dimensions=DIMS)
    repo = InMemoryRetrievalRepository()
    await RetrievalIndex(embeddings, repo).rebuild()
    return RetrievalService(embeddings, repo)


@pytest.mark.parametrize("query,filters", PARITY_CASES, ids=[c[0] for c in PARITY_CASES])
async def test_pgvector_matches_in_memory_exactly(service, in_memory_service, query, filters):
    """Both backends must return the same documents in the same order.

    Ordering matters: most queries leave many documents tied at a score of zero, and without a
    deterministic tie-break SQL returns them in physical order while the in-memory store sorts
    by id. That divergence made the same request produce different context per backend.
    """
    pg = await service.search(query, filters, limit=8)
    mem = await in_memory_service.search(query, filters, limit=8)
    assert [h.document.id for h in pg] == [h.document.id for h in mem]
    assert pg, "query returned nothing, so this comparison would be vacuous"
    by_id = {h.document.id: h.score for h in mem}
    for hit in pg:
        assert hit.score == pytest.approx(by_id[hit.document.id], abs=1e-5)


async def test_results_are_stable_across_repeated_queries(service):
    first = await service.search("card layout", RetrievalFilters(kinds=[RetrievalKind.layout]), 8)
    for _ in range(3):
        again = await service.search(
            "card layout", RetrievalFilters(kinds=[RetrievalKind.layout]), 8
        )
        assert [h.document.id for h in again] == [h.document.id for h in first]
