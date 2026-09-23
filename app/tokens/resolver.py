"""DesignIntent -> Theme -> concrete values. No LLM."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.exceptions import UnknownTokenError, ValidationError
from app.models.common import Breakpoint, Density
from app.tokens.models import ResponsiveValue, Theme, TokenCategory, TokenValue
from app.tokens.palettes import PaletteRegistry, default_palette_registry, luminance
from app.tokens.registry import ThemeRegistry

_BP_ORDER = [Breakpoint.mobile, Breakpoint.tablet, Breakpoint.desktop, Breakpoint.wide]
_DEFAULTS: dict[TokenCategory, dict[str, TokenValue]] = {
    TokenCategory.motion: {
        "duration_fast": "150ms",
        "duration_base": "300ms",
        "duration_slow": "600ms",
        "ease": "cubic-bezier(0.22, 1, 0.36, 1)",
    },
    TokenCategory.breakpoint: {"mobile": 0, "tablet": 640, "desktop": 1024, "wide": 1440},
    TokenCategory.container: {"narrow": "640px", "default": "1200px", "wide": "1440px"},
    TokenCategory.border: {"width": "1px", "style": "solid"},
}


@dataclass
class ResolvedTokens:
    theme_id: str
    values: dict[str, TokenValue] = field(default_factory=dict)  # "color.primary" -> "#..."
    responsive: dict[str, dict[Breakpoint, TokenValue]] = field(default_factory=dict)

    def get(self, key: str) -> TokenValue:
        try:
            return self.values[key]
        except KeyError:
            raise UnknownTokenError(f"unknown token: {key}", target=key) from None

    def css_variables(self) -> dict[str, str]:
        return {
            f"--{k.replace('.', '-').replace('_', '-')}": str(v) for k, v in self.values.items()
        }

    def css_variables_for(self, bp: Breakpoint) -> dict[str, str]:
        out: dict[str, str] = {}
        idx = _BP_ORDER.index(bp)
        for key, per_bp in self.responsive.items():
            for b in reversed(_BP_ORDER[: idx + 1]):  # inherit from smaller breakpoints
                if b in per_bp:
                    out[f"--{key.replace('.', '-').replace('_', '-')}"] = str(per_bp[b])
                    break
        return out


#: Type steps relative to body (0). Display is the hero headline; caption the smallest label.
TYPE_STEPS = {
    "display": 6,
    "h1": 5,
    "h2": 4,
    "h3": 3,
    "h4": 2,
    "lead": 1,
    "body": 0,
    "small": -1,
    "caption": -2,
}
_FLUID_MIN_VW, _FLUID_MAX_VW = 390, 1440  # the phone and wide-desktop widths the scale spans
_MOBILE_RATIO, _MOBILE_BASE, _DESKTOP_BASE = 1.2, 16.0, 17.0


def fluid_size(step: int, ratio: float) -> str:
    """clamp() that grows linearly from the phone size to the desktop size across viewports."""
    lo = _MOBILE_BASE * _MOBILE_RATIO**step
    hi = _DESKTOP_BASE * ratio**step
    if step <= 0 or hi <= lo:
        return f"{round(lo / 16, 4):g}rem"
    slope = (hi - lo) / (_FLUID_MAX_VW - _FLUID_MIN_VW)
    intercept = lo - slope * _FLUID_MIN_VW
    return (
        f"clamp({round(lo / 16, 4):g}rem, {round(intercept / 16, 4):g}rem + "
        f"{round(slope * 100, 4):g}vw, {round(hi / 16, 4):g}rem)"
    )


class TokenResolver:
    def __init__(self, themes: ThemeRegistry, palettes: PaletteRegistry | None = None) -> None:
        self._themes = themes
        self._palettes = palettes or default_palette_registry()

    def resolve(
        self,
        theme_id: str,
        *,
        density: Density | str = Density.comfortable,
        radius: str | None = None,
        typography: str | None = None,
        palette: str | None = None,
        overrides: dict[str, TokenValue] | None = None,
    ) -> ResolvedTokens:
        chain = self._themes.chain(theme_id)
        leaf = self._merge_scales(chain)
        merged: dict[TokenCategory, dict[str, TokenValue | ResponsiveValue]] = {
            c: dict(v) for c, v in _DEFAULTS.items()
        }
        for theme in chain:
            for cat, toks in theme.tokens.items():
                merged.setdefault(cat, {}).update(toks)

        out = ResolvedTokens(theme_id=theme_id)
        for cat, toks in merged.items():
            for name, val in toks.items():
                key = f"{cat.value}.{name}"
                if isinstance(val, ResponsiveValue):
                    out.responsive[key] = dict(val.values)
                    out.values[key] = val.values[min(val.values, key=_BP_ORDER.index)]
                else:
                    out.values[key] = val

        self._apply_palette(out, palette)
        self._apply_density(out, leaf, str(density))
        self._apply_radius(out, leaf, radius)
        self._apply_typography(out, leaf, typography)
        self._apply_overrides(out, overrides or {})
        return out

    @staticmethod
    def _merge_scales(chain: list[Theme]) -> Theme:
        """Scales/presets are inherited too: child entries override parent entries by key."""
        density: dict[str, float] = {}
        radius: dict[str, str] = {}
        typo: dict[str, dict[str, str]] = {}
        for t in chain:
            density.update(t.density_scale)
            radius.update(t.radius_scale)
            typo.update(t.typography_presets)
        return chain[-1].model_copy(
            update={"density_scale": density, "radius_scale": radius, "typography_presets": typo}
        )

    @staticmethod
    def _apply_density(out: ResolvedTokens, theme: Theme, density: str) -> None:
        if density not in theme.density_scale:
            raise ValidationError(
                f"invalid density '{density}'; allowed: {list(theme.density_scale)}",
                target="density",
            )
        factor = theme.density_scale[density]
        out.values["spacing.density_factor"] = factor
        for key in [
            k for k in out.values if k.startswith("spacing.") and k != "spacing.density_factor"
        ]:
            base = out.values[key]
            if isinstance(base, int | float):
                out.values[key] = f"{round(base * factor, 2):g}px"

    @staticmethod
    def _apply_radius(out: ResolvedTokens, theme: Theme, radius: str | None) -> None:
        chosen = radius or str(out.values.get("radius.default_scale", "medium"))
        if chosen not in theme.radius_scale:
            raise ValidationError(
                f"invalid radius '{chosen}'; allowed: {list(theme.radius_scale)}", target="radius"
            )
        base = theme.radius_scale[chosen]
        out.values["radius.base"] = base
        out.values["radius.scale"] = chosen
        # Role radii derive from one choice, so a page's corners share a single personality.
        px = 0.0 if chosen == "full" else float(base.removesuffix("px"))
        role = {"sm": px / 2, "lg": px * 1.5, "card": px, "media": px * 1.25}
        for name, value in role.items():
            out.values[f"radius.{name}"] = f"{value:g}px"
        out.values["radius.button"] = "9999px" if chosen == "full" else f"{px:g}px"
        out.values["radius.pill"] = "9999px"

    @staticmethod
    def _apply_typography(out: ResolvedTokens, theme: Theme, preset: str | None) -> None:
        chosen = preset or str(out.values.get("typography.default_preset", "modern_sans"))
        if theme.typography_presets and chosen not in theme.typography_presets:
            raise ValidationError(
                f"invalid typography '{chosen}'; allowed: {list(theme.typography_presets)}",
                target="typography",
            )
        pairing = theme.typography_presets.get(chosen, {})
        for k, v in pairing.items():
            if k != "mood":  # guidance for the Director, not a style
                out.values[f"typography.{k}"] = v
        out.values["typography.preset"] = chosen
        ratio = float(pairing.get("scale_ratio", "1.25"))
        for name, step in TYPE_STEPS.items():
            out.values[f"typography.size_{name}"] = fluid_size(step, ratio)

    def _apply_palette(self, out: ResolvedTokens, palette_id: str | None) -> None:
        """A palette replaces the theme's colours wholesale and tints its shadows."""
        if palette_id is None:
            tint = "0 0 0"
        else:
            palette = self._palettes.get(palette_id)
            for key in [k for k in out.values if k.startswith("color.")]:
                del out.values[key]
            for role, value in palette.colors.items():
                out.values[f"color.{role}"] = value
            out.values["color.mode"] = palette.mode
            tint = palette.shadow
        # Shadows need far more opacity to read on a dark background.
        bg = str(out.values.get("color.bg", "#ffffff"))
        strength = 0.35 if bg.startswith("#") and luminance(bg) < 0.2 else 0.08
        for name, (y, blur, alpha) in {
            "sm": (1, 2, 0.6),
            "md": (6, 18, 1.0),
            "lg": (16, 40, 1.3),
            "xl": (28, 70, 1.6),
        }.items():
            if out.values.get(f"shadow.{name}") == "none":
                continue  # a theme that opts out of shadows (minimal) keeps them off
            out.values[f"shadow.{name}"] = (
                f"0 {y}px {blur}px {-(y // 2)}px rgb({tint} / {round(strength * alpha, 3)})"
            )

    @staticmethod
    def _apply_overrides(out: ResolvedTokens, overrides: dict[str, TokenValue]) -> None:
        for key, val in overrides.items():
            cat = key.split(".", 1)[0]
            if cat not in TokenCategory.__members__:
                raise UnknownTokenError(f"override targets unknown category: {key}", target=key)
            out.values[key] = val
