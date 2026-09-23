"""Stock photo providers. Network, never an LLM."""

from __future__ import annotations

from typing import Any, Protocol

import httpx

from app.core.exceptions import ConfigurationError
from app.models.dsl import ImageRef


class ImageProvider(Protocol):
    async def search(self, query: str, count: int) -> list[ImageRef]: ...


class FakeImageProvider:
    """Deterministic provider for tests and offline runs: `count` photos per query, with URLs
    derived from the query. `results` pins exact answers; `fail` simulates a network outage."""

    def __init__(
        self, results: dict[str, list[ImageRef]] | None = None, *, fail: bool = False
    ) -> None:
        self.results = results
        self.fail = fail
        self.queries: list[str] = []

    async def search(self, query: str, count: int) -> list[ImageRef]:
        self.queries.append(query)
        if self.fail:
            raise httpx.ConnectError("fake provider is down")
        if self.results is not None:
            return self.results.get(query, [])[:count]
        slug = "-".join(query.lower().split())
        return [
            ImageRef(url=f"https://images.test/{slug}-{i + 1}.jpg", alt=query, credit="Fake")
            for i in range(count)
        ]


class PexelsImageProvider:
    """Pexels search API: a free key allows 200 requests an hour, one per distinct query."""

    _URL = "https://api.pexels.com/v1/search"

    def __init__(self, api_key: str, client: httpx.AsyncClient | None = None) -> None:
        self._headers = {"Authorization": api_key}
        self._client = client or httpx.AsyncClient(timeout=10.0)

    async def search(self, query: str, count: int) -> list[ImageRef]:
        response = await self._client.get(
            self._URL,
            params={"query": query, "per_page": max(1, min(count, 80))},
            headers=self._headers,
        )
        response.raise_for_status()
        return [_to_ref(p) for p in response.json().get("photos", [])]


def _to_ref(photo: dict[str, Any]) -> ImageRef:
    # large2x is 1880px wide: enough for a full-bleed hero at device scale factor 2.
    return ImageRef(
        url=photo["src"]["large2x"],
        alt=photo.get("alt") or "",
        credit=photo.get("photographer") or "",
    )


def build_image_provider(provider: str, api_key: str | None = None) -> ImageProvider | None:
    """None means no imagery: the art-directed placeholders render instead."""
    if provider == "none":
        return None
    if provider == "fake":
        return FakeImageProvider()
    if provider == "pexels":
        if not api_key:
            raise ConfigurationError(
                "UIB_IMAGE_PROVIDER=pexels needs PEXELS_API_KEY (free at pexels.com/api); "
                "set UIB_IMAGE_PROVIDER=none to keep the placeholder imagery"
            )
        return PexelsImageProvider(api_key)
    raise ConfigurationError(f"Unknown image provider: {provider}")
