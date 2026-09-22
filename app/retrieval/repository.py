"""Vector stores. In-memory for tests and local runs; pgvector for anything shared."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from typing import Any, Protocol

from app.core.exceptions import UIBuilderError
from app.retrieval.models import RetrievalDocument, RetrievalFilters, RetrievalHit


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class RetrievalRepository(Protocol):
    async def upsert(
        self, docs: Sequence[RetrievalDocument], vectors: Sequence[Sequence[float]]
    ) -> None: ...

    async def search(
        self, vector: Sequence[float], filters: RetrievalFilters, limit: int
    ) -> list[RetrievalHit]: ...

    async def count(self) -> int: ...


class InMemoryRetrievalRepository:
    def __init__(self) -> None:
        self._docs: dict[str, RetrievalDocument] = {}
        self._vectors: dict[str, list[float]] = {}

    async def upsert(
        self, docs: Sequence[RetrievalDocument], vectors: Sequence[Sequence[float]]
    ) -> None:
        if len(docs) != len(vectors):
            raise UIBuilderError("documents and vectors must be the same length")
        for doc, vec in zip(docs, vectors, strict=True):
            self._docs[doc.key] = doc
            self._vectors[doc.key] = list(vec)

    async def search(
        self, vector: Sequence[float], filters: RetrievalFilters, limit: int
    ) -> list[RetrievalHit]:
        hits = [
            RetrievalHit(document=doc, score=cosine(vector, self._vectors[key]))
            for key, doc in self._docs.items()
            if filters.matches(doc)
        ]
        hits.sort(key=lambda h: (-h.score, h.document.id))
        return hits[:limit]

    async def count(self) -> int:
        return len(self._docs)


_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS retrieval_documents (
    key          text PRIMARY KEY,
    id           text NOT NULL,
    kind         text NOT NULL,
    summary      text NOT NULL,
    text         text NOT NULL,
    metadata     jsonb NOT NULL DEFAULT '{}'::jsonb,
    embedding    vector(%(dim)s) NOT NULL
);
CREATE INDEX IF NOT EXISTS retrieval_documents_kind_idx ON retrieval_documents (kind);
CREATE INDEX IF NOT EXISTS retrieval_documents_metadata_idx
    ON retrieval_documents USING gin (metadata);
CREATE INDEX IF NOT EXISTS retrieval_documents_embedding_idx
    ON retrieval_documents USING hnsw (embedding vector_cosine_ops);
"""

_FIELDS = ("domains", "capabilities", "category", "layouts", "styles", "animations", "variants")


class PgVectorRetrievalRepository:
    """pgvector-backed store. Filtering happens in SQL so the budget applies to real candidates."""

    def __init__(self, session_factory: Any, dimensions: int) -> None:
        self._session_factory = session_factory
        self._dimensions = dimensions

    async def create_schema(self) -> None:
        from sqlalchemy import text as sql

        async with self._session_factory() as session:
            for statement in filter(None, (_SCHEMA % {"dim": self._dimensions}).split(";")):
                if statement.strip():
                    await session.execute(sql(statement))
            await session.commit()

    @staticmethod
    def _metadata(doc: RetrievalDocument) -> dict[str, Any]:
        return {f: getattr(doc, f) for f in _FIELDS}

    async def upsert(
        self, docs: Sequence[RetrievalDocument], vectors: Sequence[Sequence[float]]
    ) -> None:
        from sqlalchemy import text as sql

        rows = [
            {
                "key": d.key,
                "id": d.id,
                "kind": d.kind.value,
                "summary": d.summary,
                "text": d.text,
                "metadata": json.dumps(self._metadata(d)),
                "embedding": "[" + ",".join(map(str, v)) + "]",
            }
            for d, v in zip(docs, vectors, strict=True)
        ]
        async with self._session_factory() as session:
            await session.execute(
                sql(
                    "INSERT INTO retrieval_documents"
                    " (key, id, kind, summary, text, metadata, embedding) VALUES"
                    " (:key, :id, :kind, :summary, :text,"
                    " CAST(:metadata AS jsonb), CAST(:embedding AS vector))"
                    " ON CONFLICT (key) DO UPDATE SET summary = EXCLUDED.summary,"
                    " text = EXCLUDED.text, metadata = EXCLUDED.metadata,"
                    " embedding = EXCLUDED.embedding"
                ),
                rows,
            )
            await session.commit()

    async def search(
        self, vector: Sequence[float], filters: RetrievalFilters, limit: int
    ) -> list[RetrievalHit]:
        from sqlalchemy import text as sql

        where: list[str] = []
        params: dict[str, Any] = {
            "embedding": "[" + ",".join(map(str, vector)) + "]",
            "limit": limit,
        }
        if filters.kinds:
            where.append("kind = ANY(:kinds)")
            params["kinds"] = [k.value for k in filters.kinds]
        if filters.exclude_ids:
            where.append("id <> ALL(:exclude_ids)")
            params["exclude_ids"] = list(filters.exclude_ids)
        if filters.domain:
            where.append(
                "(jsonb_exists(metadata->'domains', '*')"
                " OR jsonb_exists(metadata->'domains', :domain))"
            )
            params["domain"] = filters.domain
        if filters.category:
            where.append("metadata->>'category' = :category")
            params["category"] = filters.category
        if filters.style:
            where.append(
                "(jsonb_array_length(metadata->'styles') = 0 "
                "OR jsonb_exists(metadata->'styles', :style))"
            )
            params["style"] = filters.style
        if filters.layout:
            where.append(
                "(jsonb_array_length(metadata->'layouts') = 0 "
                "OR jsonb_exists(metadata->'layouts', :layout))"
            )
            params["layout"] = filters.layout
        if filters.any_capabilities:
            where.append("jsonb_exists_any(metadata->'capabilities', :any_caps)")
            params["any_caps"] = list(filters.any_capabilities)
        if filters.all_capabilities:
            where.append("jsonb_exists_all(metadata->'capabilities', :all_caps)")
            params["all_caps"] = list(filters.all_capabilities)

        clause = (" WHERE " + " AND ".join(where)) if where else ""
        async with self._session_factory() as session:
            result = await session.execute(
                sql(
                    "SELECT id, kind, summary, text, metadata, "
                    "1 - (embedding <=> CAST(:embedding AS vector)) AS score "
                    f"FROM retrieval_documents{clause} "
                    "ORDER BY embedding <=> CAST(:embedding AS vector) LIMIT :limit"
                ),
                params,
            )
            hits = []
            for row in result.mappings():
                meta = (
                    row["metadata"]
                    if isinstance(row["metadata"], dict)
                    else json.loads(row["metadata"])
                )
                hits.append(
                    RetrievalHit(
                        document=RetrievalDocument(
                            id=row["id"],
                            kind=row["kind"],
                            text=row["text"],
                            summary=row["summary"],
                            **meta,
                        ),
                        score=float(row["score"]),
                    )
                )
            return hits

    async def count(self) -> int:
        from sqlalchemy import text as sql

        async with self._session_factory() as session:
            result = await session.execute(sql("SELECT count(*) FROM retrieval_documents"))
            return int(result.scalar_one())
