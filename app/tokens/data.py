"""Seed themes. Spacing tokens are stored as unitless px bases and scaled by density."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.tokens.registry import ThemeRegistry


from app.tokens.models import ResponsiveValue as R
from app.tokens.models import Theme
from app.tokens.models import TokenCategory as T

_SPACING = {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 40, "2xl": 64, "section": 96}
_TYPO_PRESETS = {
    "modern_sans": {
        "font_heading": "Inter, system-ui, sans-serif",
        "font_body": "Inter, system-ui, sans-serif",
        "heading_weight": "600",
        "heading_tracking": "-0.02em",
    },
    "geometric": {
        "font_heading": "'Space Grotesk', sans-serif",
        "font_body": "Inter, sans-serif",
        "heading_weight": "700",
        "heading_tracking": "-0.03em",
    },
    "editorial_serif": {
        "font_heading": "'Playfair Display', serif",
        "font_body": "'Source Serif 4', serif",
        "heading_weight": "500",
        "heading_tracking": "0",
    },
    "mono_accent": {
        "font_heading": "Inter, sans-serif",
        "font_body": "Inter, sans-serif",
        "font_mono": "'JetBrains Mono', monospace",
        "heading_weight": "600",
        "heading_tracking": "-0.01em",
    },
}

BASE = Theme(
    id="base",
    description="Root theme; every theme inherits from it",
    tokens={
        T.spacing: _SPACING,
        T.typography: {
            "default_preset": "modern_sans",
            "scale_ratio": 1.25,
            "base_size": "16px",
            "heading_size": R(values={"mobile": "2rem", "tablet": "2.5rem", "desktop": "3.5rem"}),
        },
        T.radius: {"default_scale": "medium"},
        T.shadow: {
            "sm": "0 1px 2px rgb(0 0 0 / 0.05)",
            "md": "0 4px 12px rgb(0 0 0 / 0.08)",
            "lg": "0 12px 32px rgb(0 0 0 / 0.12)",
        },
        T.elevation: {"flat": "0", "raised": "1", "overlay": "2"},
        T.container: {
            "default": R(
                values={"mobile": "100%", "tablet": "720px", "desktop": "1200px", "wide": "1360px"}
            )
        },
    },
    typography_presets=_TYPO_PRESETS,
)

modern_light = Theme(
    id="modern_light",
    extends="base",
    description="Clean neutral light theme",
    tokens={
        T.color: {
            "bg": "#ffffff",
            "surface": "#f8fafc",
            "fg": "#0f172a",
            "muted": "#475569",
            "primary": "#2563eb",
            "primary_fg": "#ffffff",
            "border": "#e2e8f0",
            "accent": "#7c3aed",
        }
    },
)
modern_dark = Theme(
    id="modern_dark",
    extends="modern_light",
    description="Neutral dark theme",
    tokens={
        T.color: {
            "bg": "#09090b",
            "surface": "#18181b",
            "fg": "#fafafa",
            "muted": "#a1a1aa",
            "border": "#27272a",
            # Light-on-dark: a mid blue with white text reads at 3.68:1, so the button inverts.
            "primary": "#60a5fa",
            "primary_fg": "#09090b",
            "accent": "#a78bfa",
        },
        T.shadow: {"md": "0 4px 12px rgb(0 0 0 / 0.5)", "lg": "0 12px 32px rgb(0 0 0 / 0.6)"},
    },
)
premium_light = Theme(
    id="premium_light",
    extends="modern_light",
    description="Warm, spacious, luxurious light",
    tokens={
        T.color: {
            "bg": "#fbfaf7",
            "surface": "#ffffff",
            "fg": "#1c1917",
            "muted": "#6b6560",
            "primary": "#1c1917",
            "primary_fg": "#fbfaf7",
            "accent": "#b45309",
            "border": "#e7e5e4",
        },
        T.typography: {"default_preset": "editorial_serif"},
        T.radius: {"default_scale": "large"},
        T.spacing: {"section": 128},
    },
)
premium_dark = Theme(
    id="premium_dark",
    extends="modern_dark",
    description="Deep dark with glow accents",
    tokens={
        T.color: {
            "bg": "#050505",
            "surface": "#111111",
            "primary": "#e4e4e7",
            "primary_fg": "#050505",
            "accent": "#a78bfa",
            "glow": "rgb(167 139 250 / 0.35)",
        },
        T.radius: {"default_scale": "large"},
        T.spacing: {"section": 128},
    },
)
ecommerce = Theme(
    id="ecommerce",
    extends="modern_light",
    description="High-contrast, conversion-focused",
    tokens={
        T.color: {
            "primary": "#dc2626",
            "primary_fg": "#ffffff",
            "accent": "#16a34a",
            "sale": "#dc2626",
            "rating": "#f59e0b",
        },
        T.spacing: {"section": 64},
        T.radius: {"default_scale": "small"},
    },
)
saas = Theme(
    id="saas",
    extends="modern_light",
    description="Product-led SaaS",
    tokens={
        T.color: {
            "primary": "#4f46e5",
            "accent": "#06b6d4",
            "surface": "#f5f7ff",
            "border": "#e0e7ff",
        },
        T.typography: {"default_preset": "geometric"},
    },
)
editorial = Theme(
    id="editorial",
    extends="modern_light",
    description="Long-form reading, serif",
    tokens={
        T.color: {
            "bg": "#fffdf8",
            "fg": "#111111",
            "primary": "#111111",
            "primary_fg": "#fffdf8",
            "accent": "#c2410c",
        },
        T.typography: {"default_preset": "editorial_serif", "base_size": "18px"},
        T.radius: {"default_scale": "none"},
        T.container: {"default": "760px"},
    },
)
minimal = Theme(
    id="minimal",
    extends="modern_light",
    description="Monochrome, sparse",
    tokens={
        T.color: {
            "primary": "#000000",
            "primary_fg": "#ffffff",
            "accent": "#000000",
            "surface": "#ffffff",
            "border": "#000000",
        },
        T.radius: {"default_scale": "none"},
        T.shadow: {"sm": "none", "md": "none", "lg": "none"},
        T.border: {"width": "1.5px"},
    },
)

THEMES: list[Theme] = [
    BASE,
    modern_light,
    modern_dark,
    premium_light,
    premium_dark,
    ecommerce,
    saas,
    editorial,
    minimal,
]


def default_theme_registry() -> "ThemeRegistry":
    from app.tokens.registry import ThemeRegistry

    return ThemeRegistry(THEMES)
