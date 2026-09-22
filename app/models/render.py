"""RenderModel: fully resolved, produced only by the deterministic resolver."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from app.models.common import Breakpoint, StrictModel


class ResolvedAnimation(StrictModel):
    name: str
    engine: str = "motion"
    config: dict[str, Any] = Field(default_factory=dict)
    reduced_motion_config: dict[str, Any] = Field(default_factory=dict)


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
    children: list[RenderNode] = Field(default_factory=list)


class RenderModel(StrictModel):
    screen_id: str
    theme: str
    css_variables: dict[str, str] = Field(default_factory=dict)
    root: RenderNode
    reduced_motion: bool = False


class RenderResult(StrictModel):
    html: str | None = None
    url: str | None = None
    screenshots: dict[Breakpoint, str] = Field(default_factory=dict)  # paths or base64
    dom_outline: str | None = None
    render_time_ms: float = 0.0
