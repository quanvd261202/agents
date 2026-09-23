from __future__ import annotations

from pydantic import Field

from app.layout.models import LayoutType
from app.models.common import Breakpoint, StrictModel


class RecipeSection(StrictModel):
    id: str  # section slot name, e.g. "hero"
    purpose: str
    component_types: list[str]  # allowed semantic components; first is default
    required: bool = True
    layout: LayoutType | None = None
    default_variant: str | None = None
    reorderable: bool = False  # may move within its reorder group
    reorder_group: str | None = None
    goal: str | None = None  # conversion/task goal this section serves
    content: dict[str, str] = Field(default_factory=dict)  # default slot copy; the spec's wins


class RecipeDefinition(StrictModel):
    id: str
    page_type: str
    purpose: str
    domains: list[str] = Field(default_factory=lambda: ["*"])
    sections: list[RecipeSection]
    layout_rules: dict[str, str] = Field(
        default_factory=dict
    )  # human-readable rules enforced by validator
    responsive_rules: dict[Breakpoint, str] = Field(default_factory=dict)
    shell: LayoutType = LayoutType.stack  # how sections are composed at page level
    goals: list[str] = Field(default_factory=list)

    def section(self, section_id: str) -> RecipeSection | None:
        return next((s for s in self.sections if s.id == section_id), None)

    def required_ids(self) -> list[str]:
        return [s.id for s in self.sections if s.required]

    def optional_ids(self) -> list[str]:
        return [s.id for s in self.sections if not s.required]
