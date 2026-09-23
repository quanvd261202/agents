"""Brand palettes: named colour systems the Design Director picks from, never raw hex.

Every palette defines the same semantic roles, so any component renders under any palette. The
contrast pairs below are checked when a palette is built: a palette that fails WCAG AA cannot be
registered, so no generated page can inherit an unreadable colour pair from it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.core.exceptions import UnknownTokenError
from app.core.registry import BaseRegistry
from app.models.common import StrictModel

ROLES = (
    "bg",
    "surface",
    "surface_alt",
    "fg",
    "muted",
    "primary",
    "primary_fg",
    "accent",
    "accent_fg",
    "border",
    "ring",
    "success",
    "warning",
    "danger",
    "media_a",  # two tones for art-directed image placeholders until real imagery exists
    "media_b",
)

#: (foreground, background, minimum ratio). 4.5 is AA body text; 3.0 is AA for UI shapes.
CONTRAST_PAIRS: tuple[tuple[str, str, float], ...] = (
    ("fg", "bg", 4.5),
    ("fg", "surface", 4.5),
    ("fg", "surface_alt", 4.5),
    ("muted", "bg", 4.5),
    ("muted", "surface", 4.5),
    ("primary_fg", "primary", 4.5),
    ("accent_fg", "accent", 4.5),
    ("primary", "bg", 3.0),
    ("ring", "bg", 3.0),
    ("danger", "bg", 4.5),
)


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    channels = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class Palette(StrictModel):
    id: str
    description: str
    mode: Literal["light", "dark"]
    mood: list[str] = Field(default_factory=list)  # words the Director matches a brief against
    colors: dict[str, str]
    shadow: str  # "r g b" tint for elevation, so shadows carry the palette's warmth

    @model_validator(mode="after")
    def _complete_and_readable(self) -> Palette:
        missing = [r for r in ROLES if r not in self.colors]
        if missing:
            raise ValueError(f"palette {self.id} is missing roles {missing}")
        failures = [
            f"{fg}/{bg} {contrast(self.colors[fg], self.colors[bg]):.2f} < {need}"
            for fg, bg, need in CONTRAST_PAIRS
            if contrast(self.colors[fg], self.colors[bg]) < need
        ]
        if failures:
            raise ValueError(f"palette {self.id} fails WCAG AA: {failures}")
        return self


_LIGHT_STATUS = {"success": "#1f7a4d", "warning": "#8a5a00", "danger": "#b42318"}
_DARK_STATUS = {"success": "#4ade80", "warning": "#fbbf24", "danger": "#f87171"}


def _p(
    id: str,
    description: str,
    mode: Literal["light", "dark"],
    mood: list[str],
    shadow: str,
    **colors: str,
) -> Palette:
    status = _LIGHT_STATUS if mode == "light" else _DARK_STATUS
    return Palette(
        id=id,
        description=description,
        mode=mode,
        mood=mood,
        shadow=shadow,
        colors={**status, **colors},
    )


PALETTES: list[Palette] = [
    _p(
        "espresso",
        "Roasted browns on warm cream with a terracotta accent",
        "light",
        ["coffee", "warm", "artisan", "premium", "cozy", "editorial"],
        "59 37 24",
        bg="#f7f1e8",
        surface="#fffaf3",
        surface_alt="#efe4d4",
        fg="#221a14",
        muted="#6b5a4b",
        primary="#3b2518",
        primary_fg="#fbf5ec",
        accent="#a8431c",
        accent_fg="#ffffff",
        border="#e2d4c1",
        ring="#a8431c",
        media_a="#c9a27e",
        media_b="#5b3a26",
    ),
    _p(
        "espresso_night",
        "Espresso after dark: deep roast with crema highlights",
        "dark",
        ["coffee", "warm", "premium", "moody", "night"],
        "0 0 0",
        bg="#17110d",
        surface="#211913",
        surface_alt="#2c211a",
        fg="#f5ebe0",
        muted="#bca893",
        primary="#e9c79f",
        primary_fg="#17110d",
        accent="#e2875c",
        accent_fg="#17110d",
        border="#3a2c22",
        ring="#e9c79f",
        media_a="#8a5a3c",
        media_b="#2c1b12",
    ),
    _p(
        "matcha",
        "Tea greens on rice-paper white",
        "light",
        ["tea", "fresh", "calm", "natural", "wellness", "japanese"],
        "47 74 42",
        bg="#f3f5ee",
        surface="#fbfcf8",
        surface_alt="#e3e9d8",
        fg="#1b2417",
        muted="#525c4b",
        primary="#2f4a2a",
        primary_fg="#f3f5ee",
        accent="#6f7d24",
        accent_fg="#ffffff",
        border="#d7dfca",
        ring="#2f4a2a",
        media_a="#a9bf8a",
        media_b="#3d5a33",
    ),
    _p(
        "porcelain",
        "Cool neutral whites with a precise cobalt accent",
        "light",
        ["minimal", "clean", "modern", "precise", "saas", "neutral"],
        "15 23 42",
        bg="#ffffff",
        surface="#f6f7f9",
        surface_alt="#eceef2",
        fg="#0e1116",
        muted="#566070",
        primary="#111318",
        primary_fg="#ffffff",
        accent="#3451d1",
        accent_fg="#ffffff",
        border="#e2e5ea",
        ring="#3451d1",
        media_a="#cdd5e3",
        media_b="#5d6b85",
    ),
    _p(
        "midnight",
        "Deep blue-black with luminous periwinkle, for technical products",
        "dark",
        ["tech", "developer", "ai", "futuristic", "saas", "night"],
        "0 0 0",
        bg="#0b0d12",
        surface="#131722",
        surface_alt="#1b2030",
        fg="#eef1f7",
        muted="#a0a9bb",
        primary="#8ab4ff",
        primary_fg="#0b0d12",
        accent="#c49bff",
        accent_fg="#0b0d12",
        border="#262c3b",
        ring="#8ab4ff",
        media_a="#3a4a8c",
        media_b="#151a2e",
    ),
    _p(
        "noir",
        "Near-black with champagne gold, for luxury and fashion",
        "dark",
        ["luxury", "fashion", "exclusive", "elegant", "jewelry", "night"],
        "0 0 0",
        bg="#0c0b0a",
        surface="#161412",
        surface_alt="#201d1a",
        fg="#f4efe8",
        muted="#aaa196",
        primary="#d8b27a",
        primary_fg="#0c0b0a",
        accent="#efe2cc",
        accent_fg="#0c0b0a",
        border="#2d2925",
        ring="#d8b27a",
        media_a="#6e5a3e",
        media_b="#1d1915",
    ),
    _p(
        "citrus",
        "Sunny cream with tangerine energy",
        "light",
        ["energetic", "playful", "young", "food", "summer", "bold"],
        "120 60 0",
        bg="#fffdf6",
        surface="#ffffff",
        surface_alt="#fff1c9",
        fg="#1a1a1a",
        muted="#5a574d",
        primary="#1a1a1a",
        primary_fg="#fffdf6",
        accent="#ff7a2e",
        accent_fg="#1a1a1a",
        border="#ece3c8",
        ring="#d45500",
        media_a="#ffc46b",
        media_b="#e0561c",
    ),
    _p(
        "sage",
        "Soft sage and clay, grounded and unhurried",
        "light",
        ["wellness", "calm", "organic", "home", "natural", "spa"],
        "62 90 71",
        bg="#f5f4ef",
        surface="#fbfaf6",
        surface_alt="#e6e8de",
        fg="#1f2620",
        muted="#59625a",
        primary="#3e5a47",
        primary_fg="#ffffff",
        accent="#a45a3c",
        accent_fg="#ffffff",
        border="#dadcd0",
        ring="#3e5a47",
        media_a="#b7c2ad",
        media_b="#6d5646",
    ),
    _p(
        "cobalt",
        "Electric cobalt and hot pink on white, confident and product-led",
        "light",
        ["bold", "saas", "startup", "confident", "fintech", "vibrant"],
        "42 68 255",
        bg="#ffffff",
        surface="#f5f7ff",
        surface_alt="#e8edff",
        fg="#0a0f2c",
        muted="#4a5170",
        primary="#2a44ff",
        primary_fg="#ffffff",
        accent="#c8205c",
        accent_fg="#ffffff",
        border="#dde3f5",
        ring="#2a44ff",
        media_a="#9fb0ff",
        media_b="#2a2f8f",
    ),
    _p(
        "blush",
        "Rose and berry on warm white, for beauty and fashion",
        "light",
        ["beauty", "fashion", "romantic", "soft", "feminine", "boutique"],
        "80 30 40",
        bg="#fbf6f4",
        surface="#fffdfc",
        surface_alt="#f3e5e0",
        fg="#2a1d1f",
        muted="#6c585b",
        primary="#2a1d1f",
        primary_fg="#fbf6f4",
        accent="#b33a57",
        accent_fg="#ffffff",
        border="#eadad4",
        ring="#b33a57",
        media_a="#e8bcb4",
        media_b="#7a3444",
    ),
    _p(
        "graphite",
        "Neutral charcoal with a mint signal colour",
        "dark",
        ["neutral", "tech", "gaming", "sport", "night", "modern"],
        "0 0 0",
        bg="#121212",
        surface="#1c1c1c",
        surface_alt="#262626",
        fg="#f2f2f2",
        muted="#a8a8a8",
        primary="#f2f2f2",
        primary_fg="#121212",
        accent="#4ade80",
        accent_fg="#121212",
        border="#303030",
        ring="#4ade80",
        media_a="#3d3d3d",
        media_b="#1a1a1a",
    ),
]


class PaletteRegistry(BaseRegistry[Palette]):
    kind = "palette"
    not_found_error = UnknownTokenError


def default_palette_registry() -> PaletteRegistry:
    return PaletteRegistry(PALETTES)
