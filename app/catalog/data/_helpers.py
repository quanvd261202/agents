"""Shared shorthands for the per-category catalog modules."""

from app.catalog.models import ComponentCategory as C
from app.catalog.models import (
    ComponentDefinition,
    DesignMetadata,
    ImplementationMapping,
    ResponsiveBehavior,
)
from app.catalog.models import ImplementationPart as P
from app.catalog.models import SlotDefinition as S

__all__ = [
    "C",
    "ComponentDefinition",
    "DesignMetadata",
    "ResponsiveBehavior",
    "S",
    "_ALL",
    "_CARD_ANIMS",
    "_impl",
]

_ALL = ["*"]
_CARD_ANIMS = ["fade", "fade_up", "scale", "stagger", "reveal"]


def _impl(
    root: str, *parts: tuple[str, str] | tuple[str, str, str], **props: str | int | bool
) -> ImplementationMapping:
    return ImplementationMapping(
        root=root,
        parts=[P(name=p[0], library=p[1], role=p[2] if len(p) > 2 else "") for p in parts],
        default_props=props,
    )
