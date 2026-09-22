from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field, field_validator

from app.models.common import Breakpoint, StrictModel


class LayoutType(StrEnum):
    container = "container"
    stack = "stack"
    row = "row"
    grid = "grid"
    split_ = "split"
    sidebar = "sidebar"
    bento = "bento"
    centered = "centered"
    full_bleed = "full_bleed"
    media_text = "media_text"
    card_grid = "card_grid"
    asymmetric_grid = "asymmetric_grid"


Gap = Literal["none", "xs", "sm", "md", "lg", "xl", "2xl"]
Alignment = Literal["start", "center", "end", "stretch", "baseline"]
Distribution = Literal["start", "center", "end", "between", "around", "evenly"]
MaxWidth = Literal["narrow", "default", "wide", "full"]
Padding = Literal["none", "sm", "md", "lg", "section"]

VALID_RATIOS = {"50/50", "40/60", "60/40", "30/70", "70/30", "33/67", "67/33", "25/75", "75/25"}
MAX_COLUMNS = 6


class LayoutSpec(StrictModel):
    """Semantic layout description. Never x/y/width/height."""

    type: LayoutType
    gap: Gap = "md"
    alignment: Alignment = "stretch"
    distribution: Distribution = "start"
    columns: int | None = None
    ratio: str | None = None
    max_width: MaxWidth = "default"
    padding: Padding = "md"
    density: Literal["compact", "comfortable", "spacious"] | None = None
    media_position: Literal["left", "right"] = "left"
    sidebar_position: Literal["left", "right"] = "left"
    responsive: dict[Breakpoint, LayoutOverride] = Field(default_factory=dict)

    @field_validator("columns")
    @classmethod
    def _cols(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= MAX_COLUMNS):
            raise ValueError(f"columns must be 1..{MAX_COLUMNS}")
        return v

    @field_validator("ratio")
    @classmethod
    def _ratio(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_RATIOS:
            raise ValueError(f"invalid ratio '{v}'; allowed: {sorted(VALID_RATIOS)}")
        return v


class LayoutOverride(StrictModel):
    """Semantic per-breakpoint override. `stack` collapses any multi-column layout."""

    columns: int | None = None
    gap: Gap | None = None
    ratio: str | None = None
    collapse: Literal["stack", "scroll", "hide_secondary"] | None = None
    padding: Padding | None = None


class LayoutDefinition(StrictModel):
    """Registry entry describing what a primitive supports and how it nests."""

    id: str
    description: str
    supports_columns: bool = False
    supports_ratio: bool = False
    default_columns: int | None = None
    default_ratio: str | None = None
    min_children: int = 0
    max_children: int | None = None
    allowed_children: list[LayoutType] = Field(
        default_factory=list
    )  # empty = any layout / leaf components
    forbidden_parents: list[LayoutType] = Field(default_factory=list)
    default_responsive: dict[Breakpoint, LayoutOverride] = Field(default_factory=dict)
    css_display: Literal["block", "flex", "grid"] = "block"


LayoutSpec.model_rebuild()
