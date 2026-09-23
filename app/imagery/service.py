"""Fills a DesignSpec's image slots with photographs. Deterministic apart from the provider."""

from __future__ import annotations

from app.core.logging import get_logger
from app.imagery.provider import ImageProvider
from app.models.dsl import DesignSpec, ImageRef, SectionSpec

log = get_logger(__name__)

#: Slots whose text describes a photograph rather than reading as copy.
IMAGE_SLOTS = frozenset({"image", "media"})


class Illustrator:
    """Satisfies app.services.interfaces.ImageryService.

    One search per distinct description, cached for the life of the service so other screens and
    the fix loop reuse it; within one page no photograph is used twice. A description that finds
    nothing, or a provider failure, leaves the placeholder in place: a missing photo is never worth
    failing the screen."""

    def __init__(self, provider: ImageProvider | None, *, per_query: int = 3) -> None:
        self._provider = provider
        self._per_query = per_query
        self._cache: dict[str, list[ImageRef]] = {}

    async def illustrate(self, spec: DesignSpec) -> DesignSpec:
        if self._provider is None:
            return spec
        used: set[str] = set()
        sections = [await self._section(s, used) for s in spec.sections]
        return spec.model_copy(update={"sections": sections})

    async def _section(self, s: SectionSpec, used: set[str]) -> SectionSpec:
        images = dict(s.images)
        for slot in sorted(IMAGE_SLOTS & set(s.content)):
            if slot in images:  # already sourced, e.g. a rerun after a fix
                used.update(r.url for r in images[slot] if r.url)
                continue
            # One photo per comma-separated entry, in order; an empty url keeps the position so a
            # list slot's third tile still gets its third photo when the second found nothing.
            refs = [await self._pick(q, used) for q in _entries(s.content[slot])]
            if any(r.url for r in refs):
                images[slot] = refs
        children = [await self._section(c, used) for c in s.children]
        if images == s.images and children == s.children:
            return s
        return s.model_copy(update={"images": images, "children": children})

    async def _pick(self, query: str, used: set[str]) -> ImageRef:
        refs = await self._search(query)
        chosen = next((r for r in refs if r.url not in used), refs[0] if refs else None)
        if chosen is None:
            return ImageRef(url="")
        used.add(chosen.url)
        return chosen

    async def _search(self, query: str) -> list[ImageRef]:
        assert self._provider is not None
        key = query.lower()
        if key not in self._cache:
            try:
                self._cache[key] = await self._provider.search(query, self._per_query)
            except Exception as e:  # noqa: BLE001 - transient: not cached, not fatal
                log.warning("imagery.search_failed", query=query, error=str(e))
                return []
        return self._cache[key]


def _entries(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]
