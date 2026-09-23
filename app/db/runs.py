"""Run stages: every graph node's output, per run, in order. What the requirement, plan,
direction, DSL, render, verification and fixes looked like at each step of a run."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from app.core.config import Settings
from app.db.session import build_session_factory, prepare
from app.services.repositories import RunRepository

Stage = tuple[str, dict[str, object]]


class InMemoryRunRepository:
    def __init__(self) -> None:
        self._runs: dict[str, list[Stage]] = defaultdict(list)

    async def save_stage(self, run_id: str, stage: str, payload: dict[str, object]) -> None:
        self._runs[run_id].append((stage, payload))

    async def stages(self, run_id: str) -> list[Stage]:
        return list(self._runs.get(run_id, []))


_SCHEMA = """
CREATE TABLE IF NOT EXISTS run_stages (
    id         bigserial PRIMARY KEY,
    run_id     text NOT NULL,
    stage      text NOT NULL,
    payload    jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS run_stages_run_idx ON run_stages (run_id, id);
"""


class PgRunRepository:
    def __init__(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    async def create_schema(self) -> None:
        from sqlalchemy import text as sql

        async with self._session_factory() as session:
            for statement in _SCHEMA.split(";"):
                if statement.strip():
                    await session.execute(sql(statement))
            await session.commit()

    async def save_stage(self, run_id: str, stage: str, payload: dict[str, object]) -> None:
        from sqlalchemy import text as sql

        async with self._session_factory() as session:
            await session.execute(
                sql(
                    "INSERT INTO run_stages (run_id, stage, payload)"
                    " VALUES (:run_id, :stage, CAST(:payload AS jsonb))"
                ),
                {"run_id": run_id, "stage": stage, "payload": json.dumps(payload, default=str)},
            )
            await session.commit()

    async def stages(self, run_id: str) -> list[Stage]:
        from sqlalchemy import text as sql

        async with self._session_factory() as session:
            result = await session.execute(
                sql("SELECT stage, payload FROM run_stages WHERE run_id = :run_id ORDER BY id"),
                {"run_id": run_id},
            )
            return [
                (row["stage"], p if isinstance(p := row["payload"], dict) else json.loads(p))
                for row in result.mappings()
            ]


async def build_run_repository(settings: Settings) -> RunRepository:
    if settings.persistence == "postgres":
        repo = PgRunRepository(build_session_factory(settings.database_url))
        if await prepare("runs", repo.create_schema()):
            return repo
    return InMemoryRunRepository()
