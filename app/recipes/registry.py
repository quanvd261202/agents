from __future__ import annotations

from app.core.exceptions import UnknownRecipeError
from app.core.registry import BaseRegistry
from app.recipes.data import RECIPES
from app.recipes.models import RecipeDefinition


class RecipeRegistry(BaseRegistry[RecipeDefinition]):
    kind = "recipe"
    not_found_error = UnknownRecipeError

    def for_domain(self, domain: str) -> list[RecipeDefinition]:
        return self.filter(lambda r: "*" in r.domains or domain in r.domains)

    def for_page_type(self, page_type: str) -> list[RecipeDefinition]:
        return self.filter(lambda r: r.page_type == page_type)


def default_recipe_registry() -> RecipeRegistry:
    return RecipeRegistry(RECIPES)
