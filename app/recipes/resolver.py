"""Recipe validation/expansion against a DesignSpec's section list. Deterministic."""

from __future__ import annotations

from app.catalog.registry import ComponentRegistry
from app.core.exceptions import ValidationError
from app.models.dsl import DesignSpec, SectionSpec
from app.recipes.models import RecipeDefinition
from app.recipes.registry import RecipeRegistry


class RecipeValidator:
    def __init__(self, recipes: RecipeRegistry, components: ComponentRegistry) -> None:
        self._recipes = recipes
        self._components = components

    def validate(self, spec: DesignSpec) -> RecipeDefinition:
        recipe = self._recipes.get(spec.recipe)
        ids = [s.id for s in spec.sections]
        if len(ids) != len(set(ids)):
            raise ValidationError("duplicate section ids", target=spec.screen_id)

        # every section must belong to the recipe and use an allowed component type
        for s in spec.sections:
            rs = recipe.section(s.id)
            if rs is None:
                raise ValidationError(
                    f"section '{s.id}' is not part of recipe {recipe.id}", target=s.id
                )
            if s.type not in rs.component_types:
                raise ValidationError(
                    f"section '{s.id}' uses {s.type}; allowed: {rs.component_types}", target=s.id
                )
            self._components.validate_variant(s.type, s.variant)

        missing = [r for r in recipe.required_ids() if r not in ids]
        if missing:
            raise ValidationError(
                f"recipe {recipe.id} missing required sections: {missing}", target=spec.screen_id
            )

        self._validate_order(recipe, ids)
        return recipe

    @staticmethod
    def _validate_order(recipe: RecipeDefinition, ids: list[str]) -> None:
        """Fixed sections keep recipe order; reorderable ones may shuffle inside their group."""
        recipe_order = {s.id: i for i, s in enumerate(recipe.sections)}
        sec = {s.id: s for s in recipe.sections}
        fixed = [i for i in ids if not sec[i].reorderable]
        if fixed != sorted(fixed, key=recipe_order.__getitem__):
            raise ValidationError(
                f"required UX hierarchy violated for recipe {recipe.id}: {fixed}", target=recipe.id
            )
        # reorderable sections must stay within the span of their group's fixed neighbours
        for i in ids:
            rs = sec[i]
            if rs.reorderable:
                group = [s.id for s in recipe.sections if s.reorder_group == rs.reorder_group]
                lo = min(recipe_order[g] for g in group)
                hi = max(recipe_order[g] for g in group)
                pos = ids.index(i)
                before = [x for x in ids[:pos] if recipe_order[x] > hi and not sec[x].reorderable]
                after = [
                    x for x in ids[pos + 1 :] if recipe_order[x] < lo and not sec[x].reorderable
                ]
                if before or after:
                    raise ValidationError(
                        f"section '{i}' moved outside its reorder group", target=i
                    )


class RecipeResolver:
    """Fills recipe defaults (variant, layout) into sections without adding sections."""

    def __init__(self, recipes: RecipeRegistry, components: ComponentRegistry) -> None:
        self._validator = RecipeValidator(recipes, components)
        self._components = components

    def resolve(self, spec: DesignSpec) -> DesignSpec:
        recipe = self._validator.validate(spec)
        sections: list[SectionSpec] = []
        for s in spec.sections:
            rs = recipe.section(s.id)
            assert rs is not None
            # Slot defaults were written for the slot's first component; a slot now offers several,
            # so each default applies only when the chosen component can take it.
            comp = self._components.get(s.type)
            update: dict[str, object] = {}
            if s.variant is None:
                fits = rs.default_variant in comp.variants
                update["variant"] = rs.default_variant if fits else comp.default_variant
            copy = {k: v for k, v in rs.content.items() if k in comp.slot_names()}
            if copy:
                update["content"] = {**copy, **s.content}
            layout_fits = rs.layout is not None and (
                not comp.supported_layouts or rs.layout.value in comp.supported_layouts
            )
            if s.layout is None and layout_fits:
                from app.models.dsl import LayoutIntent

                assert rs.layout is not None
                update["layout"] = LayoutIntent(type=rs.layout.value)
            sections.append(s.model_copy(update=update) if update else s)
        return spec.model_copy(update={"sections": sections})

    def scaffold(self, recipe_id: str, *, include_optional: bool = False) -> list[SectionSpec]:
        """Default section list for a recipe; useful for tests and deterministic fallbacks."""
        recipe = self._validator._recipes.get(recipe_id)
        return [
            SectionSpec(id=s.id, type=s.component_types[0], variant=s.default_variant)
            for s in recipe.sections
            if s.required or include_optional
        ]
