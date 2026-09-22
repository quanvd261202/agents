from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.models.common import StrictModel


class RetrievalKind(StrEnum):
    component = "component"
    layout = "layout"
    recipe = "recipe"
    lesson = "lesson"


class RetrievalDocument(StrictModel):
    """One indexed item. `text` is embedded; `metadata` drives exact filtering."""

    id: str
    kind: RetrievalKind
    text: str
    summary: str  # one compact line handed to the LLM
    domains: list[str] = Field(default_factory=lambda: ["*"])
    capabilities: list[str] = Field(default_factory=list)
    category: str | None = None
    layouts: list[str] = Field(default_factory=list)
    styles: list[str] = Field(default_factory=list)
    animations: list[str] = Field(default_factory=list)
    variants: list[str] = Field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.kind.value}:{self.id}"


class RetrievalFilters(StrictModel):
    kinds: list[RetrievalKind] = Field(default_factory=list)
    domain: str | None = None
    category: str | None = None
    style: str | None = None
    layout: str | None = None
    any_capabilities: list[str] = Field(default_factory=list)
    all_capabilities: list[str] = Field(default_factory=list)
    exclude_ids: list[str] = Field(default_factory=list)

    def matches(self, doc: RetrievalDocument) -> bool:
        if self.kinds and doc.kind not in self.kinds:
            return False
        if doc.id in self.exclude_ids:
            return False
        if self.domain and "*" not in doc.domains and self.domain not in doc.domains:
            return False
        if self.category and doc.category != self.category:
            return False
        if self.style and doc.styles and self.style not in doc.styles:
            return False
        if self.layout and doc.layouts and self.layout not in doc.layouts:
            return False
        caps = set(doc.capabilities)
        if self.any_capabilities and not caps & set(self.any_capabilities):
            return False
        if self.all_capabilities and not set(self.all_capabilities) <= caps:
            return False
        return True


class RetrievalHit(StrictModel):
    document: RetrievalDocument
    score: float


class RetrievedContext(StrictModel):
    """Compact, budgeted context handed to the Design Builder. IDs and one-liners only."""

    components: list[str] = Field(default_factory=list)
    layouts: list[str] = Field(default_factory=list)
    recipes: list[str] = Field(default_factory=list)
    lessons: list[str] = Field(default_factory=list)
    estimated_tokens: int = 0

    def component_ids(self) -> list[str]:
        return [line.split(" ", 1)[0] for line in self.components]
