"""LayoutSpec -> concrete CSS-ish config per breakpoint. Deterministic."""

from __future__ import annotations

from typing import Any

from app.core.exceptions import ValidationError
from app.layout.models import MAX_COLUMNS, LayoutOverride, LayoutSpec, LayoutType
from app.layout.registry import LayoutRegistry
from app.models.common import Breakpoint
from app.models.render import ResolvedLayout

_BP_ORDER = [Breakpoint.mobile, Breakpoint.tablet, Breakpoint.desktop, Breakpoint.wide]
_GAP_TOKEN = {
    "none": "0",
    "xs": "var(--spacing-xs)",
    "sm": "var(--spacing-sm)",
    "md": "var(--spacing-md)",
    "lg": "var(--spacing-lg)",
    "xl": "var(--spacing-xl)",
    "2xl": "var(--spacing-2xl)",
}
_PAD_TOKEN = {
    "none": "0",
    "sm": "var(--spacing-sm)",
    "md": "var(--spacing-md)",
    "lg": "var(--spacing-lg)",
    "section": "var(--spacing-section)",
}
_WIDTH_TOKEN = {
    "narrow": "var(--container-narrow)",
    "default": "var(--container-default)",
    "wide": "var(--container-wide)",
    "full": "100%",
}


def _ratio_to_tracks(ratio: str) -> str:
    a, b = ratio.split("/")
    return f"{a}fr {b}fr"


class LayoutValidator:
    def __init__(self, registry: LayoutRegistry) -> None:
        self._reg = registry

    def validate(
        self, spec: LayoutSpec, *, child_count: int, parent: LayoutType | None = None
    ) -> None:
        d = self._reg.get(spec.type.value)
        if parent is not None and parent in d.forbidden_parents:
            raise ValidationError(f"{spec.type} cannot be nested inside {parent}", target=spec.type)
        if spec.columns is not None and not d.supports_columns:
            raise ValidationError(f"{spec.type} does not support columns", target=spec.type)
        if spec.ratio is not None and not d.supports_ratio:
            raise ValidationError(f"{spec.type} does not support ratio", target=spec.type)
        if child_count < d.min_children:
            raise ValidationError(
                f"{spec.type} needs at least {d.min_children} children, got {child_count}",
                target=spec.type,
            )
        if d.max_children is not None and child_count > d.max_children:
            raise ValidationError(
                f"{spec.type} allows at most {d.max_children} children, got {child_count}",
                target=spec.type,
            )
        cols = spec.columns or d.default_columns
        if (
            cols is not None
            and child_count
            and child_count < cols
            and spec.type in (LayoutType.grid, LayoutType.card_grid)
        ):
            # allowed but pointless; not an error. Overflow is the real failure:
            pass
        for bp, ov in spec.responsive.items():
            if ov.columns is not None and (not d.supports_columns or ov.columns > MAX_COLUMNS):
                raise ValidationError(
                    f"{spec.type} responsive override for {bp}: invalid columns", target=spec.type
                )
            if ov.ratio is not None and not d.supports_ratio:
                raise ValidationError(
                    f"{spec.type} responsive override for {bp}: ratio unsupported", target=spec.type
                )
            if ov.collapse == "hide_secondary" and spec.type not in (
                LayoutType.sidebar,
                LayoutType.split_,
            ):
                raise ValidationError(
                    f"hide_secondary is only valid for sidebar/split, not {spec.type}",
                    target=spec.type,
                )
        # columns should never exceed children when children are fixed-size cards (overflow guard)
        if spec.type is LayoutType.bento and cols is not None and cols > MAX_COLUMNS:
            raise ValidationError("bento columns exceed maximum", target=spec.type)


class LayoutResolver:
    def __init__(self, registry: LayoutRegistry) -> None:
        self._reg = registry
        self._validator = LayoutValidator(registry)

    def resolve(
        self, spec: LayoutSpec, *, child_count: int = 0, parent: LayoutType | None = None
    ) -> ResolvedLayout:
        self._validator.validate(spec, child_count=child_count, parent=parent)
        d = self._reg.get(spec.type.value)
        base = self._base_props(spec, d.css_display, d.default_columns, d.default_ratio)
        overrides = {**d.default_responsive, **spec.responsive}
        # Each breakpoint carries a complete snapshot, so the renderer never merges deltas itself
        # and a collapse declared at one breakpoint cannot leak into a larger one.
        responsive: dict[Breakpoint, dict[str, Any]] = {}
        if overrides:
            for bp in _BP_ORDER:
                snapshot = dict(base)
                if bp in overrides:
                    snapshot.update(self._override_props(spec, overrides[bp], base))
                responsive[bp] = snapshot
        return ResolvedLayout(type=spec.type.value, props=base, responsive=responsive)

    @staticmethod
    def _base_props(
        spec: LayoutSpec, display: str, def_cols: int | None, def_ratio: str | None
    ) -> dict[str, Any]:
        props: dict[str, Any] = {
            "display": display,
            "gap": _GAP_TOKEN[spec.gap],
            "padding": _PAD_TOKEN[spec.padding],
            "alignItems": spec.alignment,
            "justifyContent": spec.distribution,
            "maxWidth": _WIDTH_TOKEN[spec.max_width],
        }
        if spec.type in (LayoutType.stack,):
            props["flexDirection"] = "column"
        if spec.type is LayoutType.row:
            props["flexDirection"] = "row"
            props["flexWrap"] = "wrap"
        cols = spec.columns or def_cols
        if cols is not None:
            props["columns"] = cols
            props["gridTemplateColumns"] = f"repeat({cols}, minmax(0, 1fr))"
        ratio = spec.ratio or def_ratio
        if ratio is not None:
            props["ratio"] = ratio
            tracks = _ratio_to_tracks(ratio)
            if spec.type is LayoutType.media_text and spec.media_position == "right":
                tracks = " ".join(reversed(tracks.split()))
            if spec.type is LayoutType.sidebar and spec.sidebar_position == "right":
                tracks = " ".join(reversed(tracks.split()))
            props["gridTemplateColumns"] = tracks
        if spec.type is LayoutType.bento:
            props["gridAutoFlow"] = "dense"
            props["gridAutoRows"] = "minmax(160px, auto)"
        if spec.type is LayoutType.full_bleed:
            props["maxWidth"] = "100%"
            props["width"] = "100vw"
        if spec.type is LayoutType.centered:
            props["maxWidth"] = _WIDTH_TOKEN["narrow"]
            props["marginInline"] = "auto"
            props["textAlign"] = "center"
        return props

    @staticmethod
    def _override_props(
        spec: LayoutSpec, ov: LayoutOverride, base: dict[str, Any]
    ) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if ov.collapse == "stack":
            out["gridTemplateColumns"] = "1fr"
            out["flexDirection"] = "column"
            out["columns"] = 1
        elif ov.collapse == "scroll":
            out["overflowX"] = "auto"
            out["gridAutoFlow"] = "column"
        elif ov.collapse == "hide_secondary":
            out["gridTemplateColumns"] = "1fr"
            out["secondaryHidden"] = True
        if ov.columns is not None:
            out["columns"] = ov.columns
            out["gridTemplateColumns"] = f"repeat({ov.columns}, minmax(0, 1fr))"
        if ov.ratio is not None:
            out["ratio"] = ov.ratio
            out["gridTemplateColumns"] = _ratio_to_tracks(ov.ratio)
        if ov.gap is not None:
            out["gap"] = _GAP_TOKEN[ov.gap]
        if ov.padding is not None:
            out["padding"] = _PAD_TOKEN[ov.padding]
        return out
