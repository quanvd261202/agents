from __future__ import annotations

from app.catalog.models import ComponentCategory, ComponentDefinition
from app.core.exceptions import UnknownComponentError, ValidationError
from app.core.registry import BaseRegistry


class ComponentRegistry(BaseRegistry[ComponentDefinition]):
    kind = "component"
    not_found_error = UnknownComponentError

    def search(self, query: str) -> list[ComponentDefinition]:
        q = query.lower().split()
        return self.filter(
            lambda c: any(w in c.id or w in c.description.lower() or w in c.capabilities for w in q)
        )

    def get_by_category(self, category: ComponentCategory | str) -> list[ComponentDefinition]:
        return self.filter(lambda c: c.category == category)

    def get_by_capability(self, capability: str) -> list[ComponentDefinition]:
        return self.filter(lambda c: capability in c.capabilities)

    def get_by_domain(self, domain: str) -> list[ComponentDefinition]:
        return self.filter(lambda c: c.supports_domain(domain))

    # --- validation -----------------------------------------------------------------------

    def validate_variant(self, component_id: str, variant: str | None) -> str:
        comp = self.get(component_id)
        if variant is None:
            return comp.default_variant
        if variant not in comp.variants:
            raise ValidationError(
                f"invalid variant '{variant}' for {component_id}; allowed: {comp.variants}",
                target=component_id,
            )
        return variant

    def validate_slots(self, component_id: str, provided: set[str]) -> None:
        comp = self.get(component_id)
        unknown = provided - comp.slot_names()
        if unknown:
            raise ValidationError(
                f"invalid slots for {component_id}: {sorted(unknown)}", target=component_id
            )
        missing = {s.name for s in comp.slots if s.required} - provided
        if missing:
            raise ValidationError(
                f"missing required slots for {component_id}: {sorted(missing)}", target=component_id
            )

    def validate_child(self, parent_id: str, child_id: str) -> None:
        parent = self.get(parent_id)
        self.get(child_id)  # raises UnknownComponentError
        if child_id not in parent.allowed_children:
            raise ValidationError(
                f"{child_id} is not an allowed child of {parent_id}", target=parent_id
            )

    def validate_animation(self, component_id: str, animation: str) -> None:
        comp = self.get(component_id)
        if animation not in comp.animation_capabilities:
            raise ValidationError(
                f"{component_id} does not support animation '{animation}'", target=component_id
            )
