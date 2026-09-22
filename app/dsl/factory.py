from app.animation import AnimationResolver, default_animation_registry
from app.catalog import default_component_registry
from app.dsl.resolver import DesignResolver
from app.layout import LayoutResolver, default_layout_registry
from app.recipes import RecipeResolver, default_recipe_registry
from app.tokens import TokenResolver, default_theme_registry


def default_design_resolver() -> DesignResolver:
    components = default_component_registry()
    return DesignResolver(
        components=components,
        tokens=TokenResolver(default_theme_registry()),
        layouts=LayoutResolver(default_layout_registry()),
        recipes=RecipeResolver(default_recipe_registry(), components),
        animations=AnimationResolver(default_animation_registry()),
    )
