"""AnimationEngine protocol + Motion (framer) adapter. No LLM, no keyframes from the model."""

from __future__ import annotations

from typing import Any, Protocol

from app.animation.models import AnimationDefinition, IntensityPreset
from app.animation.registry import AnimationRegistry
from app.core.exceptions import ValidationError
from app.models.common import Intensity
from app.models.dsl import AnimationIntent
from app.models.render import ResolvedAnimation

_EASE = [0.22, 1, 0.36, 1]


class AnimationEngine(Protocol):
    name: str

    def compile(
        self, definition: AnimationDefinition, preset: IntensityPreset, *, child_count: int
    ) -> dict[str, Any]: ...

    def compile_reduced(
        self, definition: AnimationDefinition, fallback: AnimationDefinition | None
    ) -> dict[str, Any]: ...


class MotionAnimationEngine:
    name = "motion"

    def compile(
        self, d: AnimationDefinition, p: IntensityPreset, *, child_count: int
    ) -> dict[str, Any]:
        if d.id == "none" or p == IntensityPreset():
            return {}
        transition: dict[str, Any] = {"duration": p.duration_ms / 1000, "ease": _EASE}
        cfg: dict[str, Any] = {"trigger": d.trigger, "once": d.once}
        if d.category == "entrance":
            initial: dict[str, Any] = {"opacity": p.opacity_from}
            animate: dict[str, Any] = {"opacity": 1}
            axis = d.extra.get("axis", "y")
            if p.distance:
                initial[axis] = p.distance
                animate[axis] = 0
            if p.scale_from != 1:
                initial["scale"], animate["scale"] = p.scale_from, 1
            if p.blur_px:
                initial["filter"], animate["filter"] = f"blur({p.blur_px}px)", "blur(0px)"
            if d.extra.get("clip"):
                initial["clipPath"], animate["clipPath"] = "inset(0 0 100% 0)", "inset(0 0 0% 0)"
            cfg |= {"initial": initial, "animate": animate, "transition": transition}
            if d.supports_stagger and child_count > 1 and p.stagger_ms:
                cfg["stagger"] = {"delayChildren": 0.05, "staggerChildren": p.stagger_ms / 1000}
        elif d.category == "scroll":
            cfg |= {"useScroll": True, "offsetFactor": p.amplitude}
        elif d.category == "ambient":
            if d.id == "marquee":
                cfg |= {
                    "animate": {"x": ["0%", "-50%"]},
                    "transition": {
                        "duration": p.duration_ms / 1000,
                        "repeat": "Infinity",
                        "ease": "linear",
                    },
                }
            elif d.id == "glow":
                cfg |= {
                    "animate": {"opacity": [1 - p.amplitude, 1, 1 - p.amplitude]},
                    "transition": {"duration": p.duration_ms / 1000, "repeat": "Infinity"},
                }
            else:
                cfg |= {
                    "animate": {"y": [-p.amplitude, p.amplitude, -p.amplitude]},
                    "transition": {
                        "duration": p.duration_ms / 1000,
                        "repeat": "Infinity",
                        "ease": "easeInOut",
                    },
                }
        elif d.category == "interaction":
            cfg |= {
                "whileHover": {"scale": 1.02},
                "strength": p.amplitude,
                "transition": transition,
                "layout": d.id == "morph",
            }
        elif d.category == "text":
            cfg |= {"component": "NumberTicker", "duration": p.duration_ms / 1000}
        return cfg

    def compile_reduced(
        self, d: AnimationDefinition, fallback: AnimationDefinition | None
    ) -> dict[str, Any]:
        if d.reduced_motion_fallback is None:
            return {"disabled": True}
        if d.reduced_motion_fallback == "static_row":
            return {"static": True, "layout": "row", "overflow": "auto"}
        if d.reduced_motion_fallback == "static_value":
            return {"static": True, "component": "StaticNumber"}
        # fade fallback: opacity only, short, preserves state transitions
        return {
            "initial": {"opacity": 0},
            "animate": {"opacity": 1},
            "transition": {"duration": 0.15},
            "trigger": d.trigger,
            "once": True,
        }


class AnimationResolver:
    def __init__(self, registry: AnimationRegistry, engine: AnimationEngine | None = None) -> None:
        self._reg = registry
        self._engine = engine or MotionAnimationEngine()

    def resolve(
        self,
        intent: AnimationIntent | None,
        *,
        child_count: int = 1,
        allowed: list[str] | None = None,
    ) -> ResolvedAnimation | None:
        if intent is None:
            return None
        d = self._reg.get(intent.name)
        if allowed is not None and d.id != "none" and d.id not in allowed:
            raise ValidationError(
                f"animation '{d.id}' not supported here; allowed: {allowed}", target=d.id
            )
        preset = d.presets.get(intent.intensity)
        if preset is None:
            raise ValidationError(
                f"animation '{d.id}' has no preset for intensity {intent.intensity}", target=d.id
            )
        fb = d.reduced_motion_fallback
        fallback = self._reg.get(fb) if fb is not None and fb in self._reg else None
        return ResolvedAnimation(
            name=d.id,
            engine=self._engine.name,
            config=self._engine.compile(d, preset, child_count=child_count),
            reduced_motion_config=self._engine.compile_reduced(d, fallback),
        )

    def resolve_page_default(self, name: str, intensity: Intensity) -> ResolvedAnimation | None:
        return self.resolve(AnimationIntent(name=name, intensity=intensity))
