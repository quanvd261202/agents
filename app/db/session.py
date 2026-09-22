"""Async SQLAlchemy engine/session wiring. Kept separate so repositories stay testable."""

from __future__ import annotations

from typing import Any

_ENGINES: dict[str, Any] = {}


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
