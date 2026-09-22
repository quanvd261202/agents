"""Embedding abstraction. Swapping providers must not touch retrieval or the agents."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Any, Protocol

from app.core.exceptions import ConfigurationError

_WORD = re.compile(r"[a-z0-9]+")


class EmbeddingProvider(Protocol):
    @property
    def dimensions(self) -> int: ...

    @property
    def name(self) -> str: ...

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


def _l2_normalise(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm else vec


class HashingEmbeddingProvider:
    """Deterministic, offline, no API key. Hashes tokens into a fixed space.

    Good enough for tests and local development: documents sharing vocabulary score
    higher than unrelated ones, and results never change between runs.
    """

    def __init__(self, dimensions: int = 256) -> None:
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def name(self) -> str:
        return f"hashing-{self._dimensions}"

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self._dimensions
        tokens = _WORD.findall(text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            idx = int.from_bytes(digest[:4], "big") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        return _l2_normalise(vec)

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class OpenAIEmbeddingProvider:
    """OpenAI embeddings. `dimensions` is supported by the text-embedding-3 family."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        base_url: str | None = None,
        batch_size: int = 128,
    ) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as e:  # pragma: no cover
            raise ConfigurationError("openai is not installed") from e
        kwargs: dict[str, Any] = {}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = AsyncOpenAI(**kwargs)
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def name(self) -> str:
        return f"{self._model}-{self._dimensions}"

    async def _call(self, texts: Sequence[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(
            model=self._model, input=list(texts), dimensions=self._dimensions
        )
        return [item.embedding for item in sorted(resp.data, key=lambda d: d.index)]

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            out.extend(await self._call(texts[start : start + self._batch_size]))
        return out

    async def embed_query(self, text: str) -> list[float]:
        return (await self._call([text]))[0]


def build_embedding_provider(
    provider: str,
    model: str = "text-embedding-3-small",
    dimensions: int = 1536,
    base_url: str | None = None,
) -> EmbeddingProvider:
    if provider == "hashing":
        return HashingEmbeddingProvider(dimensions=min(dimensions, 512))
    if provider == "openai":
        return OpenAIEmbeddingProvider(model=model, dimensions=dimensions, base_url=base_url)
    raise ConfigurationError(f"Unknown embedding provider: {provider}")
