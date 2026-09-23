"""Page motion choreography. Deterministic; no LLM.

The Builder picks at most one animation per section and the Director sets the page's intensity.
This module expands that into coordinated motion that fits each component's role (a hero's headline
reveals and its image settles on scroll; a grid's cards stagger in and lift under the pointer; a
stats band counts up) and then enforces a per-page motion budget, so motion stays intentional:
continuous, scroll-linked and attention-grabbing effects are capped, and the earliest sections win.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.animation import AnimationResolver
from app.catalog import ComponentDefinition
from app.models.common import Intensity
from app.models.dsl import AnimationIntent
from app.models.render import MotionBehavior, RenderNode

# --- component roles ----------------------------------------------------------------------
_HEADLINE = {
    "hero", "manifesto", "category_hero", "section_header", "editorial_quote", "product_spotlight",
    "promo_banner", "cta", "cta_split", "brand_story", "testimonial_spotlight", "app_download",
}  # fmt: skip
_ITEMS = {
    "product_grid", "collection_grid", "feature_bento", "testimonial_grid", "article_grid",
    "team_grid", "stats", "metrics", "steps", "integrations_grid", "press_quotes", "pricing_table",
    "related_products", "lookbook", "gallery_masonry", "menu_list", "trust_signals", "timeline",
    "social_proof", "media_text", "feature_split", "progress_list", "reviews", "subscription_offer",
    "stats_band", "faq", "comparison_table",
}  # fmt: skip
_NUMBERS = {"metrics", "stats", "stats_band", "kpi_hero", "social_proof"}
_MEDIA = {
    "hero", "image_band", "brand_story", "product_spotlight", "promo_banner", "media_text",
    "feature_split", "gallery_masonry", "lookbook", "video_showcase", "category_hero",
    "collection_grid", "cta_split", "app_download", "product_showcase", "tabs_showcase",
}  # fmt: skip
# Depth reads best on these; at expressive intensity parallax replaces their scroll zoom.
_PARALLAX = {"image_band", "brand_story", "gallery_masonry", "lookbook"}
_CARDS = {
    "product_grid", "collection_grid", "article_grid", "feature_bento", "related_products",
    "team_grid", "pricing_table", "integrations_grid", "testimonial_grid",
}  # fmt: skip
_TILT = {"product_spotlight", "hero", "app_download", "product_showcase", "collection_grid"}
_CTA = {
    "hero", "cta", "cta_split", "promo_banner", "product_spotlight", "newsletter_signup",
    "app_download",
}  # fmt: skip
_AMBIENT = {"cta", "hero", "promo_banner", "manifesto", "stats_band", "newsletter_signup"}
_STACK = {"image_band", "manifesto", "promo_banner", "stats_band", "editorial_quote"}
_SCROLL_FADE = {"rich_text", "faq", "section_header", "timeline", "article_grid"}

_ORDER = [Intensity.none, Intensity.subtle, Intensity.moderate, Intensity.expressive]


@dataclass(frozen=True)
class _Rule:
    roles: frozenset[str]
    behavior: str
    min_intensity: Intensity


# Order matters only for readability: every matching rule applies, then the budget trims.
RULES: tuple[_Rule, ...] = (
    _Rule(frozenset(_ITEMS), "stagger", Intensity.subtle),
    _Rule(frozenset(_NUMBERS), "number_ticker", Intensity.subtle),
    _Rule(frozenset(_CARDS), "lift", Intensity.subtle),
    _Rule(frozenset(_HEADLINE), "headline_reveal", Intensity.moderate),
    _Rule(frozenset(_MEDIA), "scroll_zoom", Intensity.moderate),
    _Rule(frozenset(_PARALLAX), "parallax", Intensity.expressive),
    _Rule(frozenset(_CTA), "magnetic", Intensity.moderate),
    _Rule(frozenset(_TILT), "tilt", Intensity.moderate),
    _Rule(frozenset(_AMBIENT), "gradient_drift", Intensity.expressive),
    _Rule(frozenset(_STACK), "stack", Intensity.expressive),
    _Rule(frozenset(_SCROLL_FADE), "scroll_fade", Intensity.expressive),
)

#: Which budget a behaviour spends. Cheap one-shot behaviours (stagger, count-up, lift) spend none.
BUDGET_GROUP = {
    "headline_reveal": "text",
    "scroll_zoom": "scroll",
    "scroll_fade": "scroll",
    "parallax": "scroll",
    "stack": "stack",
    "magnetic": "magnetic",
    "tilt": "tilt",
    "float": "ambient",
    "glow": "ambient",
    "gradient_drift": "ambient",
    "marquee": "ambient",
}
#: Per-page caps. Subtle pages get no attention-grabbing motion at all.
BUDGET: dict[Intensity, dict[str, int]] = {
    Intensity.none: {},
    Intensity.subtle: {"ambient": 1},
    Intensity.moderate: {"text": 2, "scroll": 3, "magnetic": 1, "tilt": 1, "ambient": 1},
    Intensity.expressive: {
        "text": 3,
        "scroll": 5,
        "stack": 1,
        "magnetic": 2,
        "tilt": 2,
        "ambient": 2,
    },
}
#: A scroll zoom and a parallax on the same image fight each other: parallax replaces the zoom.
_EXCLUSIVE = {"parallax": "scroll_zoom"}


def allowed_motion(component: ComponentDefinition) -> list[str]:
    """Everything a component may animate with: its catalog capabilities plus every behaviour the
    choreographer can give it. The Builder may pick any of these explicitly."""
    roles = [r.behavior for r in RULES if component.id in r.roles]
    return list(dict.fromkeys([*component.animation_capabilities, *roles]))


def section_nodes(root: RenderNode) -> list[RenderNode]:
    """Page sections in order, looking through the app shell's Main container."""
    out: list[RenderNode] = []
    for child in root.children:
        out.extend(child.children if child.implementation == "Main" else [child])
    return out


def choreograph(root: RenderNode, intensity: Intensity, animations: AnimationResolver) -> None:
    """Add role-based behaviours to every section, then trim the page to its motion budget.
    Behaviours already on a node (picked explicitly by the Builder) are admitted first."""
    sections = section_nodes(root)
    if intensity == Intensity.none:  # a still page is still: explicit picks included
        for node in sections:
            node.motion = []
        return
    explicit = [(i, b) for i, node in enumerate(sections) for b in node.motion]
    suggested: list[tuple[int, MotionBehavior]] = []
    level = _ORDER.index(intensity)
    for i, node in enumerate(sections):
        for rule in RULES:
            if node.semantic_type in rule.roles and level >= _ORDER.index(rule.min_intensity):
                b = animations.behavior(AnimationIntent(name=rule.behavior, intensity=intensity))
                if b is not None:
                    suggested.append((i, b))

    caps = BUDGET[intensity]
    spent: dict[str, int] = {}
    kept: dict[int, list[MotionBehavior]] = {i: [] for i in range(len(sections))}
    for i, b in [*explicit, *suggested]:
        names = {k.name for k in kept[i]}
        if b.name in names:
            continue
        group = BUDGET_GROUP.get(b.name)
        if group is not None:
            if spent.get(group, 0) >= caps.get(group, 0):
                continue
            spent[group] = spent.get(group, 0) + 1
        replaced = _EXCLUSIVE.get(b.name)
        if replaced in names:
            kept[i] = [k for k in kept[i] if k.name != replaced]
            if replaced is not None and (g := BUDGET_GROUP.get(replaced)):
                spent[g] -= 1
        kept[i].append(b)
    for i, node in enumerate(sections):
        node.motion = kept[i]
