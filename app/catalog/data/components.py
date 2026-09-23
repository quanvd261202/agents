"""Seed semantic component catalog, assembled from one module per category.

Each category module owns its components' definitions and implementation mappings; the frontend
mirrors the split in frontend/src/sections/. Implementation mappings live here, never in agents.
"""

from typing import TYPE_CHECKING

from app.catalog.data import commerce, content, data, forms, marketing, storytelling, structure
from app.catalog.models import ComponentDefinition

if TYPE_CHECKING:
    from app.catalog.registry import ComponentRegistry

COMPONENTS: list[ComponentDefinition] = [
    *structure.COMPONENTS,
    *marketing.COMPONENTS,
    *commerce.COMPONENTS,
    *content.COMPONENTS,
    *data.COMPONENTS,
    *forms.COMPONENTS,
    *storytelling.COMPONENTS,
]


def default_component_registry() -> "ComponentRegistry":
    from app.catalog.registry import ComponentRegistry

    return ComponentRegistry(COMPONENTS)
