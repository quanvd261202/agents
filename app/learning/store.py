"""Lesson stores. In-memory for tests and local runs; pgvector for anything shared across runs.
Both rank by embedding similarity inside an exact scope match, with `id` breaking ties."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from app.models.learning import Lesson
from app.retrieval.embeddings import EmbeddingProvider
from app.retrieval.repository import cosine


def _in_scope(lesson: Lesson, scope: dict[str, str]) -> bool:
    return all(lesson.scope.get(k) == v for k, v in scope.items())


class InMemoryLessonRepository:
    def __init__(self, embeddings: EmbeddingProvider) -> None:
        self._embeddings = embeddings
        self._lessons: dict[str, Lesson] = {}
        self._vectors: dict[str, list[float]] = {}

    async def search(self, query: str, scope: dict[str, str], limit: int) -> list[Lesson]:
        vector = await self._embeddings.embed_query(query)
        hits = [
            (cosine(vector, self._vectors[lid]), lid)
            for lid, lesson in self._lessons.items()
            if _in_scope(lesson, scope)
        ]
        hits.sort(key=lambda h: (-h[0], h[1]))
        return [self._lessons[lid] for _, lid in hits[:limit]]

    async def get(self, lesson_id: str) -> Lesson | None:
        return self._lessons.get(lesson_id)

    async def upsert(self, lesson: Lesson) -> None:
        self._lessons[lesson.id] = lesson
        self._vectors[lesson.id] = await self._embeddings.embed_query(lesson.text)

    async def list_all(self) -> list[Lesson]:
        return sorted(self._lessons.values(), key=lambda x: (-x.confirmations, x.id))


_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS lessons (
    id            text PRIMARY KEY,
    text          text NOT NULL,
    scope         jsonb NOT NULL DEFAULT '{}'::jsonb,
    fix           jsonb NOT NULL DEFAULT '{}'::jsonb,
    status        text NOT NULL,
    confirmations integer NOT NULL DEFAULT 0,
    violations    integer NOT NULL DEFAULT 0,
    evidence      jsonb NOT NULL DEFAULT '[]'::jsonb,
    embedding     vector(%(dim)s) NOT NULL,
    updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS lessons_scope_idx ON lessons USING gin (scope);
CREATE INDEX IF NOT EXISTS lessons_embedding_idx
    ON lessons USING hnsw (embedding vector_cosine_ops);
"""

_COLUMNS = "id, text, scope, fix, status, confirmations, violations, evidence"


class PgLessonRepository:
    """pgvector-backed store, same shape as PgVectorRetrievalRepository. The scope filter is a
    jsonb containment test, so it runs in SQL before the vector ordering."""

    def __init__(self, session_factory: Any, embeddings: EmbeddingProvider) -> None:
        self._session_factory = session_factory
        self._embeddings = embeddings

    async def create_schema(self) -> None:
        from sqlalchemy import text as sql

        async with self._session_factory() as session:
            for statement in (_SCHEMA % {"dim": self._embeddings.dimensions}).split(";"):
                if statement.strip():
                    await session.execute(sql(statement))
            await session.commit()

    @staticmethod
    def _vector(v: Sequence[float]) -> str:
        return "[" + ",".join(map(str, v)) + "]"

    async def search(self, query: str, scope: dict[str, str], limit: int) -> list[Lesson]:
        from sqlalchemy import text as sql

        vector = await self._embeddings.embed_query(query)
        async with self._session_factory() as session:
            result = await session.execute(
                sql(
                    f"SELECT {_COLUMNS} FROM lessons WHERE scope @> CAST(:scope AS jsonb)"
                    " ORDER BY embedding <=> CAST(:embedding AS vector), id LIMIT :limit"
                ),
                {"scope": json.dumps(scope), "embedding": self._vector(vector), "limit": limit},
            )
            return [_row_to_lesson(row) for row in result.mappings()]

    async def get(self, lesson_id: str) -> Lesson | None:
        from sqlalchemy import text as sql

        async with self._session_factory() as session:
            result = await session.execute(
                sql(f"SELECT {_COLUMNS} FROM lessons WHERE id = :id"), {"id": lesson_id}
            )
            row = result.mappings().first()
            return _row_to_lesson(row) if row else None

    async def upsert(self, lesson: Lesson) -> None:
        from sqlalchemy import text as sql

        vector = await self._embeddings.embed_query(lesson.text)
        async with self._session_factory() as session:
            await session.execute(
                sql(
                    "INSERT INTO lessons (id, text, scope, fix, status, confirmations, violations,"
                    " evidence, embedding) VALUES (:id, :text, CAST(:scope AS jsonb),"
                    " CAST(:fix AS jsonb), :status, :confirmations, :violations,"
                    " CAST(:evidence AS jsonb), CAST(:embedding AS vector))"
                    " ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text, scope = EXCLUDED.scope,"
                    " fix = EXCLUDED.fix, status = EXCLUDED.status,"
                    " confirmations = EXCLUDED.confirmations, violations = EXCLUDED.violations,"
                    " evidence = EXCLUDED.evidence, embedding = EXCLUDED.embedding,"
                    " updated_at = now()"
                ),
                {
                    "id": lesson.id,
                    "text": lesson.text,
                    "scope": json.dumps(lesson.scope),
                    "fix": json.dumps(lesson.fix),
                    "status": lesson.status,
                    "confirmations": lesson.confirmations,
                    "violations": lesson.violations,
                    "evidence": json.dumps(lesson.evidence),
                    "embedding": self._vector(vector),
                },
            )
            await session.commit()

    async def list_all(self) -> list[Lesson]:
        from sqlalchemy import text as sql

        async with self._session_factory() as session:
            result = await session.execute(
                sql(f"SELECT {_COLUMNS} FROM lessons ORDER BY confirmations DESC, id")
            )
            return [_row_to_lesson(row) for row in result.mappings()]


def _json(value: Any) -> Any:
    return value if isinstance(value, dict | list) else json.loads(value)


def _row_to_lesson(row: Any) -> Lesson:
    return Lesson(
        id=row["id"],
        text=row["text"],
        scope=_json(row["scope"]),
        fix=_json(row["fix"]),
        status=row["status"],
        confirmations=row["confirmations"],
        violations=row["violations"],
        evidence=_json(row["evidence"]),
    )
