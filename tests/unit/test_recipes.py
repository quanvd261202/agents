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
        "brand_page",
        "ecommerce_home",
        "ecommerce_listing",
        "ecommerce_product",
        "ecommerce_cart",
        "ecommerce_checkout",
    }


def test_generic_recipes_are_the_fallback_for_an_unserved_domain():
    reg = default_recipe_registry()
    assert [r.id for r in reg.for_domain("blog")] == ["saas_landing", "brand_page"]
    assert "saas_landing" in {r.id for r in reg.for_domain("saas")}  # claims saas explicitly


def test_recipe_copy_fills_empty_slots_and_the_spec_wins():
    from app.catalog import default_component_registry
    from app.models import DesignSpec
    from app.recipes.resolver import RecipeResolver
    from tests.fixtures.specs import ECOMMERCE_HOME

    spec = DesignSpec.model_validate(ECOMMERCE_HOME)
    spec = spec.model_copy(
        update={
            "sections": [
                s.model_copy(update={"content": {"headline": "Beans, roasted Tuesday"}})
                if s.id == "hero"
                else s
                for s in spec.sections
            ]
        }
    )
    out = RecipeResolver(default_recipe_registry(), default_component_registry()).resolve(spec)
    assert out.find("navigation").content["actions"] == "Cart"  # shop nav, not "Get started"
    hero = out.find("hero").content
    assert hero["headline"] == "Beans, roasted Tuesday"  # the spec's own copy wins
    assert hero["primary_cta"] == "Shop now"  # the recipe fills what the spec left empty


def test_every_component_a_recipe_offers_resolves_in_that_slot():
    """A slot may carry a layout (e.g. bento); a component offered there that cannot take that
    layout would only fail at render time, on a page an agent already built."""
    from app.catalog import default_component_registry
    from app.dsl import default_design_resolver
    from app.models import DesignSpec
    from app.models.dsl import SectionSpec
    from app.recipes.resolver import RecipeResolver

    recipes = default_recipe_registry()
    scaffold = RecipeResolver(recipes, default_component_registry())
    resolver = default_design_resolver()
    failures = []
    for recipe in recipes:
        base = scaffold.scaffold(recipe.id)
        for slot in recipe.sections:
            for comp in slot.component_types:
                sections = [s for s in base if s.id != slot.id]
                order = [s.id for s in recipe.sections]
                sections.append(SectionSpec(id=slot.id, type=comp))
                sections.sort(key=lambda s: order.index(s.id))
                spec = DesignSpec(
                    screen_id="s",
                    recipe=recipe.id,
                    visual_style="v",
                    theme="modern_light",
                    sections=sections,
                )
                try:
                    resolver.resolve(spec)
                except Exception as e:  # noqa: BLE001 - collect every failure, then report
                    failures.append(f"{recipe.id}.{slot.id} <- {comp}: {e}")
    assert not failures, "\n".join(failures)
