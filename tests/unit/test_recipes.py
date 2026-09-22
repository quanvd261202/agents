import pytest

from app.catalog import default_component_registry
from app.core.exceptions import UnknownRecipeError, ValidationError
from app.models import DesignSpec
from app.recipes import RecipeResolver, default_recipe_registry


@pytest.fixture
def resolver() -> RecipeResolver:
    return RecipeResolver(default_recipe_registry(), default_component_registry())


def _spec(recipe: str, sections: list[dict]) -> DesignSpec:
    return DesignSpec(
        screen_id="s", recipe=recipe, visual_style="modern", theme="modern_light", sections=sections
    )


def test_seed_recipes_reference_known_components():
    comps = default_component_registry()
    for r in default_recipe_registry():
        for s in r.sections:
            for t in s.component_types:
                assert comps.exists(t), f"{r.id}.{s.id} -> {t}"


def test_scaffold_for_every_recipe_validates(resolver):
    for r in default_recipe_registry():
        for opt in (False, True):
            spec = _spec(
                r.id, [s.model_dump() for s in resolver.scaffold(r.id, include_optional=opt)]
            )
            out = resolver.resolve(spec)
            assert all(s.variant is not None for s in out.sections)


def test_defaults_filled(resolver):
    out = resolver.resolve(
        _spec(
            "saas_landing",
            [
                {"id": "navigation", "type": "navigation"},
                {"id": "hero", "type": "hero"},
                {"id": "features", "type": "feature_bento"},
                {"id": "cta", "type": "cta"},
                {"id": "footer", "type": "footer"},
            ],
        )
    )
    hero = out.find("hero")
    assert hero.layout.type == "split" and hero.variant == "standard"


def test_missing_required_section(resolver):
    with pytest.raises(ValidationError, match="missing required"):
        resolver.resolve(
            _spec(
                "saas_landing",
                [{"id": "navigation", "type": "navigation"}, {"id": "footer", "type": "footer"}],
            )
        )


def test_unknown_section_or_wrong_type(resolver):
    base = [
        {"id": "navigation", "type": "navigation"},
        {"id": "hero", "type": "hero"},
        {"id": "features", "type": "feature_bento"},
        {"id": "cta", "type": "cta"},
        {"id": "footer", "type": "footer"},
    ]
    with pytest.raises(ValidationError, match="not part of recipe"):
        resolver.resolve(
            _spec("saas_landing", base + [{"id": "danger_zone", "type": "danger_zone"}])
        )
    with pytest.raises(ValidationError, match="allowed"):
        resolver.resolve(
            _spec("saas_landing", [{**base[1], "type": "product_detail"}] + base[:1] + base[2:])
        )


def test_required_hierarchy_cannot_be_destroyed(resolver):
    # footer before hero
    with pytest.raises(ValidationError, match="hierarchy"):
        resolver.resolve(
            _spec(
                "saas_landing",
                [
                    {"id": "navigation", "type": "navigation"},
                    {"id": "footer", "type": "footer"},
                    {"id": "hero", "type": "hero"},
                    {"id": "features", "type": "feature_bento"},
                    {"id": "cta", "type": "cta"},
                ],
            )
        )


def test_reorder_within_group_allowed_but_not_outside(resolver):
    ok = [
        {"id": "navigation", "type": "navigation"},
        {"id": "hero", "type": "hero"},
        {"id": "metrics", "type": "metrics"},
        {"id": "features", "type": "feature_bento"},
        {"id": "cta", "type": "cta"},
        {"id": "footer", "type": "footer"},
    ]
    resolver.resolve(_spec("saas_landing", ok))
    bad = [ok[0], ok[2], ok[1], ok[3], ok[4], ok[5]]  # metrics before hero
    with pytest.raises(ValidationError):
        resolver.resolve(_spec("saas_landing", bad))


def test_unknown_recipe(resolver):
    with pytest.raises(UnknownRecipeError):
        resolver.resolve(_spec("blog", [{"id": "x", "type": "hero"}]))


def test_domain_filter():
    assert {r.id for r in default_recipe_registry().for_domain("ecommerce")} == {
        "saas_landing",
        "ecommerce_product",
    }
