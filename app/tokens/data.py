"""Seed themes. Spacing tokens are stored as unitless px bases and scaled by density."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.tokens.registry import ThemeRegistry


from app.tokens.models import ResponsiveValue as R
from app.tokens.models import Theme
from app.tokens.models import TokenCategory as T

_SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 40,
    "2xl": 64,
    "3xl": 96,
    "section": 96,
}
# Font pairings. Family names are the self-hosted @fontsource families the frontend bundles, so a
# render never depends on a font CDN. `scale_ratio` drives the fluid type scale at desktop; mobile
# always uses a tighter ratio so display type still fits a phone.
_TYPO_PRESETS = {
    "modern_sans": {
        "font_heading": "'Inter Variable', system-ui, sans-serif",
        "font_body": "'Inter Variable', system-ui, sans-serif",
        "heading_weight": "600",
        "heading_tracking": "-0.03em",
        "scale_ratio": "1.25",
        "mood": "neutral, product, clean",
    },
    "geometric": {
        "font_heading": "'Space Grotesk Variable', sans-serif",
        "font_body": "'Inter Variable', sans-serif",
        "heading_weight": "600",
        "heading_tracking": "-0.035em",
        "scale_ratio": "1.3",
        "mood": "technical, startup, confident",
    },
    "editorial_serif": {
        "font_heading": "'Fraunces Variable', Georgia, serif",
        "font_body": "'Inter Variable', system-ui, sans-serif",
        "heading_weight": "480",
        "heading_tracking": "-0.02em",
        "scale_ratio": "1.333",
        "mood": "editorial, warm, artisan, premium",
    },
    "luxe_serif": {
        "font_heading": "'Cormorant Garamond', Georgia, serif",
        "font_body": "'Manrope Variable', system-ui, sans-serif",
        "heading_weight": "500",
        "heading_tracking": "-0.01em",
        "scale_ratio": "1.414",
        "mood": "luxury, fashion, refined",
    },
    "classic_serif": {
        "font_heading": "'Playfair Display Variable', Georgia, serif",
        "font_body": "'DM Sans Variable', system-ui, sans-serif",
        "heading_weight": "600",
        "heading_tracking": "-0.015em",
        "scale_ratio": "1.333",
        "mood": "classic, trustworthy, heritage",
    },
    "grotesk_display": {
        "font_heading": "'Bricolage Grotesque Variable', sans-serif",
        "font_body": "'DM Sans Variable', system-ui, sans-serif",
        "heading_weight": "700",
        "heading_tracking": "-0.04em",
        "scale_ratio": "1.414",
        "mood": "energetic, young, bold, contemporary",
    },
    "humanist": {
        "font_heading": "'DM Sans Variable', system-ui, sans-serif",
        "font_body": "'DM Sans Variable', system-ui, sans-serif",
        "heading_weight": "650",
        "heading_tracking": "-0.03em",
        "scale_ratio": "1.25",
        "mood": "friendly, approachable, wellness",
    },
    "expressive": {
        "font_heading": "'Syne', sans-serif",
        "font_body": "'Manrope Variable', system-ui, sans-serif",
        "heading_weight": "700",
        "heading_tracking": "-0.02em",
        "scale_ratio": "1.5",
        "mood": "creative, agency, avant-garde",
    },
    "mono_accent": {
        "font_heading": "'JetBrains Mono Variable', ui-monospace, monospace",
        "font_body": "'Inter Variable', system-ui, sans-serif",
        "font_mono": "'JetBrains Mono Variable', ui-monospace, monospace",
        "heading_weight": "600",
        "heading_tracking": "-0.02em",
        "scale_ratio": "1.25",
        "mood": "developer, technical, terminal",
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
            "surface_alt": "#eef2f7",
            "accent_fg": "#ffffff",
            "ring": "#2563eb",
            "success": "#1f7a4d",
            "warning": "#8a5a00",
            "danger": "#b42318",
            "media_a": "#c7d2fe",
            "media_b": "#3730a3",
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
            "accent_fg": "#09090b",
            "surface_alt": "#27272a",
            "ring": "#60a5fa",
            "success": "#4ade80",
            "warning": "#fbbf24",
            "danger": "#f87171",
            "media_a": "#3f3f46",
            "media_b": "#18181b",
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
            "surface_alt": "#f1ede6",
            "ring": "#1c1917",
            "media_a": "#d6c4ad",
            "media_b": "#57534e",
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
            "surface_alt": "#1c1c1c",
            "ring": "#e4e4e7",
            "media_a": "#3b3355",
            "media_b": "#111111",
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
            # Mid green: dark text reads 5.8:1 on it, white only 3.3:1.
            "accent_fg": "#052e16",
            "ring": "#dc2626",
            "media_a": "#fecaca",
            "media_b": "#7f1d1d",
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
            # Cyan is light: white text on it fails AA, deep teal passes.
            "accent_fg": "#083344",
            "surface": "#f5f7ff",
            "surface_alt": "#e8edff",
            "ring": "#4f46e5",
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
