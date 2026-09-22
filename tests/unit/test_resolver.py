import pytest

from app.core.exceptions import (
    ResolutionError,
    UnknownComponentError,
    UnknownRecipeError,
    UnknownTokenError,
    ValidationError,
)
from app.dsl import default_design_resolver
from app.models import DesignSpec, RenderNode
from tests.fixtures.specs import ALL, SAAS_LANDING


@pytest.fixture(scope="module")
def resolver():
    return default_design_resolver()


def _walk(n: RenderNode):
    yield n
    for c in n.children:
        yield from _walk(c)


@pytest.mark.parametrize("name", list(ALL))
def test_golden_specs_resolve(resolver, name):
    spec = DesignSpec.model_validate(ALL[name])
    model = resolver.resolve(spec)
    assert model.screen_id == spec.screen_id
    nodes = list(_walk(model.root))
    assert all(n.implementation for n in nodes)  # every node has a concrete React component
    assert all(
        n.props.get("variant") for n in nodes if n.id not in ("page", "main")
    )  # defaults filled
    assert "--color-primary" in model.css_variables
    ids = [n.id for n in nodes]
    assert len(ids) == len(set(ids))


def test_expansion_is_much_larger_than_dsl(resolver):
    spec = DesignSpec.model_validate(SAAS_LANDING)
    model = resolver.resolve(spec)
    assert len(model.model_dump_json()) > 4 * len(spec.model_dump_json())


def test_deterministic(resolver):
    spec = DesignSpec.model_validate(SAAS_LANDING)
    assert resolver.resolve(spec).model_dump() == resolver.resolve(spec).model_dump()


def test_page_animation_applies_to_sections_and_can_be_overridden(resolver):
    model = resolver.resolve(DesignSpec.model_validate(SAAS_LANDING))
    by_id = {n.id: n for n in _walk(model.root)}
    assert by_id["hero"].animation.name == "stagger"  # page default (subtle_stagger alias)
    assert by_id["social_proof"].animation.name == "marquee"  # section override
    assert by_id["metrics"].animation.config["component"] == "NumberTicker"
    assert by_id["features"].animation.config["stagger"]["staggerChildren"] > 0  # 4 children


def test_recipe_layout_defaults_and_component_responsive_hints(resolver):
    model = resolver.resolve(DesignSpec.model_validate(ALL["ecommerce_product"]))
    by_id = {n.id: n for n in _walk(model.root)}
    assert by_id["product_detail"].layout.props["gridTemplateColumns"] == "60fr 40fr"
    assert by_id["product_detail"].layout.responsive["mobile"]["columns"] == 1
    assert model.root.layout.type == "stack"
    dash = resolver.resolve(DesignSpec.model_validate(ALL["dashboard"]))
    assert dash.root.layout.type == "sidebar"
    stats = next(n for n in _walk(dash.root) if n.id == "stats")
    assert stats.layout.props["columns"] == 4 and stats.layout.responsive["tablet"]["columns"] == 2


def test_reduced_motion_flag(resolver):
    model = resolver.resolve(DesignSpec.model_validate(SAAS_LANDING), reduced_motion=True)
    assert model.reduced_motion is True
    hero = next(n for n in _walk(model.root) if n.id == "hero")
    assert hero.animation.reduced_motion_config["animate"] == {"opacity": 1}


def _bad(**over):
    return DesignSpec.model_validate({**SAAS_LANDING, **over})


def test_invalid_inputs_rejected(resolver):
    with pytest.raises(UnknownRecipeError):
        resolver.resolve(_bad(recipe="blog"))
    with pytest.raises(UnknownTokenError):
        resolver.resolve(_bad(theme="neon"))
    with pytest.raises(ValidationError):  # unknown component type inside a recipe section
        resolver.resolve(
            _bad(
                sections=[{**SAAS_LANDING["sections"][0], "type": "motion.div"}]
                + SAAS_LANDING["sections"][1:]
            )
        )
    with pytest.raises(ValidationError):  # invalid variant
        resolver.resolve(
            _bad(
                sections=[{**SAAS_LANDING["sections"][1], "variant": "neon"}]
                + [SAAS_LANDING["sections"][0]]
                + SAAS_LANDING["sections"][2:]
            )
        )
    with pytest.raises(ValidationError):  # unsupported layout for hero
        s = [dict(x) for x in SAAS_LANDING["sections"]]
        s[1]["layout"] = {"type": "bento"}
        resolver.resolve(_bad(sections=s))
    with pytest.raises(ValidationError):  # invalid slot
        s = [dict(x) for x in SAAS_LANDING["sections"]]
        s[1]["content"] = {"headline": "x", "confetti": "y"}
        resolver.resolve(_bad(sections=s))
    with pytest.raises(ValidationError):  # animation not supported by footer
        s = [dict(x) for x in SAAS_LANDING["sections"]]
        s[-1]["animation"] = {"name": "parallax"}
        resolver.resolve(_bad(sections=s))
    with pytest.raises((ValidationError, UnknownComponentError)):  # bad child
        s = [dict(x) for x in SAAS_LANDING["sections"]]
        s[3] = {**s[3], "children": [{"id": "z", "type": "hero"}]}
        resolver.resolve(_bad(sections=s))


def test_unexpected_failure_is_structured(resolver, monkeypatch):
    monkeypatch.setattr(resolver._tokens, "resolve", lambda *a, **k: 1 / 0)
    with pytest.raises(ResolutionError):
        resolver.resolve(DesignSpec.model_validate(SAAS_LANDING))
