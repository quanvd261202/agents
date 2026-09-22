from __future__ import annotations

from typing import Any

from pydantic import Field

from app.models.common import Intensity, StrictModel


class IntensityPreset(StrictModel):
    distance: float = 0.0  # px translate
    scale_from: float = 1.0
    duration_ms: int = 300
    stagger_ms: int = 0
    opacity_from: float = 1.0
    amplitude: float = 0.0  # for float/parallax/glow
    blur_px: float = 0.0


class AnimationDefinition(StrictModel):
    id: str
    description: str
    category: str  # entrance | ambient | interaction | text | scroll
    presets: dict[Intensity, IntensityPreset]
    trigger: str = "in_view"  # in_view | mount | hover | scroll | always
    once: bool = True
    supports_stagger: bool = False
    essential: bool = False  # kept (simplified) under reduced motion because it conveys state/info
    reduced_motion_fallback: str | None = "fade"  # None = disable entirely
    extra: dict[str, Any] = Field(default_factory=dict)
