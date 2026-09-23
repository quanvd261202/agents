"""Graph checkpointing. Postgres when persistence asks for it and answers, else in memory.

A checkpoint after every node means the clarification round trip sends only the answers on the
second pass, and every stage of a run can be inspected afterwards by its thread id (the run id)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import app.models as models
from app.core.config import Settings
from app.core.logging import get_logger
from app.models.common import Breakpoint, Density, Dimension, Intensity, Severity
from app.retrieval.models import RetrievedContext

log = get_logger(__name__)


def serializer() -> Any:
    """Checkpoints hold our Pydantic models and enums, so they are allow-listed explicitly rather
    than accepted with a warning; anything else in a checkpoint is refused."""
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    allowed = [
        *(getattr(models, name) for name in models.__all__),
        RetrievedContext,
        Breakpoint,
        Density,
        Dimension,
        Intensity,
        Severity,
    ]
    return JsonPlusSerializer(allowed_msgpack_modules=allowed)


def psycopg_url(database_url: str) -> str:
    """The SQLAlchemy URL names the asyncpg driver; the LangGraph saver speaks psycopg."""
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


@asynccontextmanager
async def checkpointer_for(settings: Settings) -> AsyncIterator[Any]:
    from langgraph.checkpoint.memory import InMemorySaver

    serde = serializer()
    if settings.persistence == "postgres":
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            async with AsyncPostgresSaver.from_conn_string(
                psycopg_url(settings.database_url), serde=serde
            ) as saver:
                await saver.setup()
                yield saver
                return
        except Exception as e:  # noqa: BLE001 - degrade, never fail the run over persistence
            log.warning("persistence.unavailable", store="checkpoints", error=str(e))
    yield InMemorySaver(serde=serde)
