from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.models.common import Breakpoint, StrictModel

TokenValue = str | int | float


class TokenCategory(StrEnum):
    color = "color"
    typography = "typography"
    spacing = "spacing"
    radius = "radius"
    shadow = "shadow"
    border = "border"
    elevation = "elevation"
    motion = "motion"
    breakpoint = "breakpoint"
    container = "container"


class ResponsiveValue(StrictModel):
    """A token whose concrete value differs per breakpoint. Missing keys inherit smaller."""

    values: dict[Breakpoint, TokenValue]


TokenSet = dict[str, TokenValue | ResponsiveValue]


class Theme(StrictModel):
    id: str
    description: str = ""
    extends: str | None = None
    tokens: dict[TokenCategory, dict[str, TokenValue | ResponsiveValue]] = Field(
        default_factory=dict
    )
    # Semantic scales the LLM may pick from; resolved against tokens.
    density_scale: dict[str, float] = Field(
        default_factory=lambda: {"compact": 0.75, "comfortable": 1.0, "spacious": 1.35}
    )
    radius_scale: dict[str, str] = Field(
        default_factory=lambda: {
            "none": "0px",
            "small": "4px",
            "medium": "8px",
            "large": "16px",
            "full": "9999px",
        }
    )
    typography_presets: dict[str, dict[str, str]] = Field(default_factory=dict)
