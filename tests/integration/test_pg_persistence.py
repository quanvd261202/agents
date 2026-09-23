"""Lesson store and run stages against a real Postgres. Skipped when no database is reachable."""

from __future__ import annotations

import socket
from urllib.parse import urlparse

import pytest

from app.core.config import Settings
from app.db import PgRunRepository, build_session_factory, dispose_engine
from app.learning import InMemoryLessonRepository, PgLessonRepository
from app.models import Lesson
from app.retrieval import HashingEmbeddingProvider

pytest.importorskip("sqlalchemy")
pytest.importorskip("asyncpg")

DB_URL = Settings(_env_file=None).database_url


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

SCOPE = {"domain": "ecommerce", "page_type": "storefront", "component": "product_grid"}
LESSONS = [
    Lesson(
        id=f"it-{i}",
        text=f"product_grid on storefront pages: narrow columns fixed by columns={i}",
        scope={**SCOPE, "problem": f"p{i}"},
        fix={"property": "columns", "value": str(i)},
        status="trusted" if i == 3 else "candidate",
        confirmations=i,
    )
    for i in (2, 3)
] + [
    Lesson(
        id="it-saas",
        text="feature_bento on landing pages: clipped text fixed by variant=standard",
        scope={"domain": "saas", "page_type": "landing", "component": "feature_bento"},
        fix={"property": "variant", "value": "standard"},
    )
]


@pytest.fixture
async def factory():
    f = build_session_factory(DB_URL)
    yield f
    await dispose_engine(DB_URL)


async def test_lessons_round_trip_and_search_in_scope(factory):
    embeddings = HashingEmbeddingProvider(64)
    pg = PgLessonRepository(factory, embeddings)
    await pg.create_schema()
    mem = InMemoryLessonRepository(embeddings)
    for lesson in LESSONS:
        await pg.upsert(lesson)
        await mem.upsert(lesson)

    assert await pg.get("it-3") == LESSONS[1]
    assert await pg.get("missing") is None
    query = "narrow columns product grid"
    assert [x.id for x in await pg.search(query, SCOPE, 10)] == [
        x.id for x in await mem.search(query, SCOPE, 10)
    ]
    assert {x.id for x in await pg.search(query, SCOPE, 10)} == {"it-2", "it-3"}
    assert [x.id for x in await pg.search(query, {**SCOPE, "problem": "p3"}, 10)] == ["it-3"]

    promoted = LESSONS[0].model_copy(update={"confirmations": 5, "status": "trusted"})
    await pg.upsert(promoted)
    assert await pg.get("it-2") == promoted  # upsert replaces, never duplicates
    assert {x.id for x in await pg.list_all()} >= {"it-2", "it-3", "it-saas"}


async def test_run_stages_round_trip_in_order(factory):
    repo = PgRunRepository(factory)
    await repo.create_schema()
    run_id = "it-run-" + str(id(repo))
    await repo.save_stage(run_id, "clarifier", {"clarified_requirements": {"domain": "saas"}})
    await repo.save_stage(run_id, "home/renderer", {"render_result": {"render_time_ms": 12.5}})
    assert await repo.stages(run_id) == [
        ("clarifier", {"clarified_requirements": {"domain": "saas"}}),
        ("home/renderer", {"render_result": {"render_time_ms": 12.5}}),
    ]
    assert await repo.stages("no-such-run") == []
