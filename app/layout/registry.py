from __future__ import annotations

from app.core.exceptions import UnknownLayoutError
from app.core.registry import BaseRegistry
from app.layout.models import LayoutDefinition, LayoutOverride, LayoutType

_STACK_MOBILE = {"mobile": LayoutOverride(collapse="stack")}

LAYOUTS: list[LayoutDefinition] = [
    LayoutDefinition(
        id="container", description="Max-width wrapper with horizontal padding", max_children=1
    ),
    LayoutDefinition(id="stack", description="Vertical flow", css_display="flex"),
    LayoutDefinition(
        id="row",
        description="Horizontal flow, wraps on small screens",
        css_display="flex",
        default_responsive=_STACK_MOBILE,
    ),
    LayoutDefinition(
        id="grid",
        description="Uniform column grid",
        supports_columns=True,
        default_columns=3,
        css_display="grid",
        default_responsive={
            "mobile": LayoutOverride(columns=1),
            "tablet": LayoutOverride(columns=2),
        },
    ),
    LayoutDefinition(
        id="split",
        description="Two panes with a ratio",
        supports_ratio=True,
        default_ratio="50/50",
        min_children=2,
        max_children=2,
        css_display="grid",
        default_responsive=_STACK_MOBILE,
    ),
    LayoutDefinition(
        id="sidebar",
        description="Fixed sidebar + fluid main",
        supports_ratio=True,
        default_ratio="25/75",
        min_children=2,
        max_children=2,
        css_display="grid",
        forbidden_parents=[LayoutType.sidebar, LayoutType.split_, LayoutType.centered],
        default_responsive={
            "mobile": LayoutOverride(collapse="hide_secondary"),
            "tablet": LayoutOverride(ratio="30/70"),
        },
    ),
    LayoutDefinition(
        id="bento",
        description="Mixed-span feature grid",
        supports_columns=True,
        default_columns=4,
        css_display="grid",
        min_children=3,
        forbidden_parents=[LayoutType.bento, LayoutType.split_, LayoutType.sidebar],
        default_responsive={
            "mobile": LayoutOverride(columns=1),
            "tablet": LayoutOverride(columns=2),
        },
    ),
    LayoutDefinition(
        id="centered",
        description="Narrow centered column",
        max_children=1,
        forbidden_parents=[LayoutType.centered, LayoutType.split_, LayoutType.sidebar],
    ),
    LayoutDefinition(
        id="full_bleed",
        description="Edge-to-edge band",
        max_children=1,
        forbidden_parents=[
            LayoutType.container,
            LayoutType.centered,
            LayoutType.split_,
            LayoutType.sidebar,
            LayoutType.grid,
            LayoutType.bento,
        ],
    ),
    LayoutDefinition(
        id="media_text",
        description="Media beside text",
        supports_ratio=True,
        default_ratio="50/50",
        min_children=2,
        max_children=2,
        css_display="grid",
        default_responsive=_STACK_MOBILE,
    ),
    LayoutDefinition(
        id="card_grid",
        description="Auto-fit card grid",
        supports_columns=True,
        default_columns=3,
        css_display="grid",
        forbidden_parents=[LayoutType.card_grid, LayoutType.bento],
        default_responsive={
            "mobile": LayoutOverride(columns=1),
            "tablet": LayoutOverride(columns=2),
        },
    ),
    LayoutDefinition(
        id="asymmetric_grid",
        description="Editorial grid with unequal tracks",
        supports_columns=True,
        default_columns=3,
        css_display="grid",
        forbidden_parents=[LayoutType.asymmetric_grid, LayoutType.bento, LayoutType.split_],
        default_responsive={
            "mobile": LayoutOverride(columns=1),
            "tablet": LayoutOverride(columns=2),
        },
    ),
]


class LayoutRegistry(BaseRegistry[LayoutDefinition]):
    kind = "layout"
    not_found_error = UnknownLayoutError


def default_layout_registry() -> LayoutRegistry:
    return LayoutRegistry(LAYOUTS)
