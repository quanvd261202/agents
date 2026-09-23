"""RenderModel: fully resolved, produced only by the deterministic resolver."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.models.common import Breakpoint, StrictModel
from app.models.verification import Issue


class ResolvedAnimation(StrictModel):
    name: str
    engine: str = "motion"
    config: dict[str, Any] = Field(default_factory=dict)
    reduced_motion_config: dict[str, Any] = Field(default_factory=dict)


class MotionBehavior(StrictModel):
    """One runtime motion behaviour on a section: a headline reveal, a scroll zoom, a hover tilt.
    Chosen by name from the animation vocabulary; the frontend motion runtime executes it."""

    name: str
    params: dict[str, float | int | str] = Field(default_factory=dict)


class ResolvedLayout(StrictModel):
    type: str
    props: dict[str, Any] = Field(default_factory=dict)
    responsive: dict[Breakpoint, dict[str, Any]] = Field(default_factory=dict)


class RenderNode(StrictModel):
    id: str
    semantic_type: str
    implementation: str
    props: dict[str, Any] = Field(default_factory=dict)
    tokens: dict[str, str] = Field(default_factory=dict)  # css var references
    layout: ResolvedLayout | None = None
    animation: ResolvedAnimation | None = None
    #: Behaviours layered on the entrance: the choreographer's expansion of the section's motion.
    motion: list[MotionBehavior] = Field(default_factory=list)
    children: list[RenderNode] = Field(default_factory=list)


class RenderModel(StrictModel):
    screen_id: str
    theme: str
    #: The screen's route in the site, when it was resolved as part of one.
    route: str | None = None
    css_variables: dict[str, str] = Field(default_factory=dict)
    root: RenderNode
    reduced_motion: bool = False


class RenderResult(StrictModel):
    html: str | None = None
    url: str | None = None
    screenshots: dict[Breakpoint, str] = Field(default_factory=dict)  # paths or base64
    dom_outline: str | None = None
    render_time_ms: float = 0.0
    #: Deterministic in-page checks. The verifier treats these as authoritative.
    findings: list[Issue] = Field(default_factory=list)
