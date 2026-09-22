from __future__ import annotations

from app.animation.models import AnimationDefinition
from app.animation.models import IntensityPreset as P
from app.core.exceptions import UnknownAnimationError
from app.core.registry import BaseRegistry
from app.models.common import Intensity as I


def _entrance(
    dist: tuple[float, float, float],
    dur: tuple[int, int, int],
    scale: tuple[float, float, float] = (1, 1, 1),
) -> dict[I, P]:
    return {
        I.none: P(),
        I.subtle: P(
            distance=dist[0], duration_ms=dur[0], opacity_from=0, scale_from=scale[0], stagger_ms=60
        ),
        I.moderate: P(
            distance=dist[1], duration_ms=dur[1], opacity_from=0, scale_from=scale[1], stagger_ms=90
        ),
        I.expressive: P(
            distance=dist[2],
            duration_ms=dur[2],
            opacity_from=0,
            scale_from=scale[2],
            stagger_ms=120,
            blur_px=8,
        ),
    }


def _ambient(amp: tuple[float, float, float], dur: tuple[int, int, int]) -> dict[I, P]:
    return {
        I.none: P(),
        **{
            lvl: P(amplitude=a, duration_ms=d)
            for lvl, a, d in zip((I.subtle, I.moderate, I.expressive), amp, dur, strict=True)
        },
    }


ANIMATIONS: list[AnimationDefinition] = [
    AnimationDefinition(
        id="none",
        description="No animation",
        category="entrance",
        presets={i: P() for i in I},
        reduced_motion_fallback=None,
    ),
    AnimationDefinition(
        id="fade",
        description="Opacity in",
        category="entrance",
        presets=_entrance((0, 0, 0), (300, 450, 600)),
        supports_stagger=True,
    ),
    AnimationDefinition(
        id="fade_up",
        description="Fade + rise",
        category="entrance",
        presets=_entrance((12, 24, 48), (350, 500, 700)),
        supports_stagger=True,
    ),
    AnimationDefinition(
        id="fade_down",
        description="Fade + drop",
        category="entrance",
        presets=_entrance((-12, -24, -48), (350, 500, 700)),
        supports_stagger=True,
    ),
    AnimationDefinition(
        id="scale",
        description="Scale in",
        category="entrance",
        presets=_entrance((0, 0, 0), (300, 450, 600), (0.97, 0.92, 0.85)),
        supports_stagger=True,
    ),
    AnimationDefinition(
        id="reveal",
        description="Clip-path reveal",
        category="entrance",
        presets=_entrance((0, 0, 0), (500, 700, 900)),
        extra={"clip": True},
    ),
    AnimationDefinition(
        id="stagger",
        description="Children enter sequentially",
        category="entrance",
        presets=_entrance((8, 16, 32), (300, 400, 550)),
        supports_stagger=True,
    ),
    AnimationDefinition(
        id="slide",
        description="Slide from side",
        category="entrance",
        presets=_entrance((24, 48, 96), (350, 500, 700)),
        extra={"axis": "x"},
    ),
    AnimationDefinition(
        id="parallax",
        description="Scroll-linked depth",
        category="scroll",
        trigger="scroll",
        once=False,
        presets=_ambient((0.05, 0.12, 0.25), (0, 0, 0)),
        reduced_motion_fallback=None,
    ),
    AnimationDefinition(
        id="float",
        description="Gentle continuous drift",
        category="ambient",
        trigger="always",
        once=False,
        presets=_ambient((4, 8, 16), (4000, 3500, 3000)),
        reduced_motion_fallback=None,
    ),
    AnimationDefinition(
        id="glow",
        description="Pulsing glow",
        category="ambient",
        trigger="always",
        once=False,
        presets=_ambient((0.2, 0.4, 0.7), (3000, 2500, 2000)),
        reduced_motion_fallback=None,
    ),
    AnimationDefinition(
        id="marquee",
        description="Infinite horizontal scroll",
        category="ambient",
        trigger="always",
        once=False,
        presets=_ambient((30, 50, 80), (40000, 30000, 20000)),
        essential=True,
        reduced_motion_fallback="static_row",
    ),
    AnimationDefinition(
        id="magnetic",
        description="Cursor-attracted button",
        category="interaction",
        trigger="hover",
        once=False,
        presets=_ambient((4, 8, 14), (200, 200, 200)),
        reduced_motion_fallback=None,
    ),
    AnimationDefinition(
        id="morph",
        description="Layout morph between states",
        category="interaction",
        trigger="mount",
        once=False,
        presets=_ambient((0, 0, 0), (250, 350, 500)),
        essential=True,
        reduced_motion_fallback="fade",
    ),
    AnimationDefinition(
        id="number_ticker",
        description="Count up numbers",
        category="text",
        presets=_ambient((0, 0, 0), (800, 1200, 1800)),
        essential=True,
        reduced_motion_fallback="static_value",
    ),
]


class AnimationRegistry(BaseRegistry[AnimationDefinition]):
    kind = "animation"
    not_found_error = UnknownAnimationError


def default_animation_registry() -> AnimationRegistry:
    return AnimationRegistry(ANIMATIONS)
