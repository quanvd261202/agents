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


# --- M8: behaviours the frontend motion runtime executes -----------------------------------
def _levels(**by_level: P) -> dict[I, P]:
    return {I.none: P(), **{I(k): v for k, v in by_level.items()}}


ANIMATIONS += [
    AnimationDefinition(
        id="blur_in",
        description="Fade in from a soft blur",
        category="entrance",
        presets=_levels(
            subtle=P(opacity_from=0, blur_px=6, duration_ms=450, stagger_ms=60),
            moderate=P(opacity_from=0, blur_px=10, distance=12, duration_ms=600, stagger_ms=80),
            expressive=P(opacity_from=0, blur_px=16, distance=24, duration_ms=800, stagger_ms=110),
        ),
        supports_stagger=True,
    ),
    AnimationDefinition(
        id="headline_reveal",
        description="Headline words rise into place from behind a mask",
        category="text",
        presets=_levels(
            subtle=P(distance=100, duration_ms=700, stagger_ms=30),
            moderate=P(distance=110, duration_ms=900, stagger_ms=55),
            expressive=P(distance=120, duration_ms=1100, stagger_ms=80),
        ),
        reduced_motion_fallback="fade",
    ),
    AnimationDefinition(
        id="scroll_zoom",
        description="Imagery settles from a slight zoom as it scrolls into view",
        category="scroll",
        trigger="scroll",
        once=False,
        presets=_levels(
            subtle=P(scale_from=1.06), moderate=P(scale_from=1.12), expressive=P(scale_from=1.2)
        ),
        reduced_motion_fallback=None,
    ),
    AnimationDefinition(
        id="scroll_fade",
        description="Content rises and brightens as it scrolls into view",
        category="scroll",
        trigger="scroll",
        once=False,
        presets=_levels(
            subtle=P(distance=24, opacity_from=0.5),
            moderate=P(distance=40, opacity_from=0.35),
            expressive=P(distance=64, opacity_from=0.2),
        ),
        reduced_motion_fallback=None,
    ),
    AnimationDefinition(
        id="stack",
        description="The section pins and recedes as the next one slides over it",
        category="scroll",
        trigger="scroll",
        once=False,
        presets=_levels(
            subtle=P(scale_from=0.97), moderate=P(scale_from=0.94), expressive=P(scale_from=0.9)
        ),
        reduced_motion_fallback=None,
    ),
    AnimationDefinition(
        id="lift",
        description="Cards rise and deepen their shadow under the pointer",
        category="interaction",
        trigger="hover",
        once=False,
        presets=_levels(
            subtle=P(distance=3, duration_ms=200),
            moderate=P(distance=6, duration_ms=250),
            expressive=P(distance=10, duration_ms=300),
        ),
        reduced_motion_fallback=None,
    ),
    AnimationDefinition(
        id="tilt",
        description="Imagery tilts in 3D toward the pointer",
        category="interaction",
        trigger="hover",
        once=False,
        presets=_levels(subtle=P(amplitude=3), moderate=P(amplitude=6), expressive=P(amplitude=10)),
        reduced_motion_fallback=None,
    ),
    AnimationDefinition(
        id="gradient_drift",
        description="A soft brand-coloured light slowly drifts behind the section",
        category="ambient",
        trigger="always",
        once=False,
        presets=_levels(
            subtle=P(amplitude=0.15, duration_ms=16000),
            moderate=P(amplitude=0.25, duration_ms=12000),
            expressive=P(amplitude=0.4, duration_ms=9000),
        ),
        reduced_motion_fallback=None,
    ),
]


class AnimationRegistry(BaseRegistry[AnimationDefinition]):
    kind = "animation"
    not_found_error = UnknownAnimationError


def default_animation_registry() -> AnimationRegistry:
    return AnimationRegistry(ANIMATIONS)
