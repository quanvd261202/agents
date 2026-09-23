"""Async SQLAlchemy engine/session wiring. Kept separate so repositories stay testable."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import Any

from app.core.logging import get_logger

log = get_logger(__name__)

_ENGINES: dict[str, Any] = {}

#: How long to wait for Postgres before a run continues with in-memory persistence.
CONNECT_TIMEOUT_S = 5.0


def build_session_factory(database_url: str, echo: bool = False) -> Any:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = _ENGINES.get(database_url)
    if engine is None:
        engine = create_async_engine(database_url, echo=echo, pool_pre_ping=True)
        _ENGINES[database_url] = engine
    return async_sessionmaker(engine, expire_on_commit=False)


async def dispose_engine(database_url: str) -> None:
    engine = _ENGINES.pop(database_url, None)
    if engine is not None:
        await engine.dispose()


async def prepare(store: str, create_schema: Awaitable[None]) -> bool:
    """Create a store's schema if the database answers in time. False means the caller falls
    back to memory: an unreachable database costs one run's persistence, never the run."""
    try:
        await asyncio.wait_for(create_schema, CONNECT_TIMEOUT_S)
        return True
    except Exception as e:  # noqa: BLE001 - degrade, never fail the run over persistence
        log.warning("persistence.unavailable", store=store, error=str(e))
        return False
