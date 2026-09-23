"""Central Design DSL: the contract between the LLM and the deterministic engine."""

from __future__ import annotations

from pydantic import Field

from app.models.common import Density, Intensity, StrictModel


class LayoutIntent(StrictModel):
    type: str
    columns: int | None = None
    ratio: str | None = None
    gap: str | None = None
    alignment: str | None = None
    max_width: str | None = None


class AnimationIntent(StrictModel):
    name: str
    intensity: Intensity = Intensity.subtle


class SectionSpec(StrictModel):
    id: str
    type: str
    variant: str | None = None
    layout: LayoutIntent | None = None
    animation: AnimationIntent | None = None
    children: list[SectionSpec] = Field(default_factory=list)
    content: dict[str, str] = Field(default_factory=dict)


class DesignSpec(StrictModel):
    screen_id: str
    recipe: str
    visual_style: str
    theme: str
    density: Density = Density.comfortable
    # Brand axes, named from the token registries; None falls back to the theme's defaults.
    palette: str | None = None
    typography: str | None = None
    radius: str | None = None
    sections: list[SectionSpec] = Field(min_length=1)
    animation: AnimationIntent | None = None

    def find(self, section_id: str) -> SectionSpec | None:
        stack = list(self.sections)
        while stack:
            s = stack.pop()
            if s.id == section_id:
                return s
            stack.extend(s.children)
        return None
