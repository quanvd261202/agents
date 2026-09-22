"""DesignIntent -> Theme -> concrete values. No LLM."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.exceptions import UnknownTokenError, ValidationError
from app.models.common import Breakpoint, Density
from app.tokens.models import ResponsiveValue, Theme, TokenCategory, TokenValue
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


class TokenResolver:
    def __init__(self, themes: ThemeRegistry) -> None:
        self._themes = themes

    def resolve(
        self,
        theme_id: str,
        *,
        density: Density | str = Density.comfortable,
        radius: str | None = None,
        typography: str | None = None,
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
        out.values["radius.base"] = theme.radius_scale[chosen]
        out.values["radius.scale"] = chosen

    @staticmethod
    def _apply_typography(out: ResolvedTokens, theme: Theme, preset: str | None) -> None:
        chosen = preset or str(out.values.get("typography.default_preset", "modern_sans"))
        if theme.typography_presets and chosen not in theme.typography_presets:
            raise ValidationError(
                f"invalid typography '{chosen}'; allowed: {list(theme.typography_presets)}",
                target="typography",
            )
        for k, v in theme.typography_presets.get(chosen, {}).items():
            out.values[f"typography.{k}"] = v
        out.values["typography.preset"] = chosen

    @staticmethod
    def _apply_overrides(out: ResolvedTokens, overrides: dict[str, TokenValue]) -> None:
        for key, val in overrides.items():
            cat = key.split(".", 1)[0]
            if cat not in TokenCategory.__members__:
                raise UnknownTokenError(f"override targets unknown category: {key}", target=key)
            out.values[key] = val
