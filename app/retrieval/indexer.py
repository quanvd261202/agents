"""Turns the registries into indexable documents. The only place catalog wording is shaped."""

from __future__ import annotations

from app.catalog import ComponentDefinition, ComponentRegistry, default_component_registry
from app.layout import LayoutDefinition, LayoutRegistry, default_layout_registry
from app.recipes import RecipeDefinition, RecipeRegistry, default_recipe_registry
from app.retrieval.models import RetrievalDocument, RetrievalKind


def _component_doc(c: ComponentDefinition) -> RetrievalDocument:
    text = " ".join(
        [
            c.id.replace("_", " "),
            c.description,
            c.category.value,
            " ".join(c.capabilities),
            " ".join(c.supported_layouts),
            " ".join(c.design_metadata.visual_styles),
            " ".join(v.replace("_", " ") for v in c.variants),
            c.design_metadata.conversion_role or "",
        ]
    )
    return RetrievalDocument(
        id=c.id,
        kind=RetrievalKind.component,
        text=text,
        summary=f"{c.id} ({c.category.value}): {c.description} | variants: {', '.join(c.variants)}",
        domains=list(c.supported_domains),
        capabilities=list(c.capabilities),
        category=c.category.value,
        layouts=list(c.supported_layouts),
        styles=list(c.design_metadata.visual_styles),
        animations=list(c.animation_capabilities),
        variants=list(c.variants),
    )


def _layout_doc(layout: LayoutDefinition) -> RetrievalDocument:
    traits = []
    if layout.supports_columns:
        traits.append(f"columns (default {layout.default_columns})")
    if layout.supports_ratio:
        traits.append(f"ratio (default {layout.default_ratio})")
    return RetrievalDocument(
        id=layout.id,
        kind=RetrievalKind.layout,
        text=f"{layout.id.replace('_', ' ')} {layout.description} {' '.join(traits)}",
        summary=f"{layout.id}: {layout.description}"
        + (f" | {', '.join(traits)}" if traits else ""),
        layouts=[layout.id],
    )


def _recipe_doc(r: RecipeDefinition) -> RetrievalDocument:
    sections = ", ".join(s.id for s in r.sections)
    return RetrievalDocument(
        id=r.id,
        kind=RetrievalKind.recipe,
        text=f"{r.id.replace('_', ' ')} {r.page_type} {r.purpose} {' '.join(r.goals)} {sections}",
        summary=f"{r.id} ({r.page_type}): {r.purpose} | sections: {sections}",
        domains=list(r.domains),
        capabilities=list(r.goals),
    )


def build_documents(
    components: ComponentRegistry | None = None,
    layouts: LayoutRegistry | None = None,
    recipes: RecipeRegistry | None = None,
) -> list[RetrievalDocument]:
    components = components or default_component_registry()
    layouts = layouts or default_layout_registry()
    recipes = recipes or default_recipe_registry()
    return (
        [_component_doc(c) for c in components]
        + [_layout_doc(v) for v in layouts]
        + [_recipe_doc(r) for r in recipes]
    )
