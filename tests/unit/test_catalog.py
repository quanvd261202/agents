import pytest

from app.catalog import ComponentDefinition, ComponentRegistry, default_component_registry
from app.catalog.models import ImplementationMapping
from app.core.exceptions import UnknownComponentError, ValidationError
from app.core.registry import DuplicateIdError


def _comp(cid: str, **kw) -> ComponentDefinition:
    return ComponentDefinition(
        id=cid,
        category="marketing",
        description=cid,
        implementation=ImplementationMapping(root="X"),
        **kw,
    )


@pytest.fixture
def reg() -> ComponentRegistry:
    return default_component_registry()


def test_seed_catalog_has_unique_ids_and_leaf_children_exist(reg):
    for c in reg:
        for child in c.allowed_children:
            assert reg.exists(child), f"{c.id} references unknown child {child}"
    assert len(reg) >= 25


def test_register_and_duplicate():
    r = ComponentRegistry()
    r.register(_comp("a"))
    assert r.exists("a") and r.get("a").id == "a"
    with pytest.raises(DuplicateIdError):
        r.register(_comp("a"))


def test_unknown_component(reg):
    with pytest.raises(UnknownComponentError):
        reg.get("motion.div")


def test_variant_validation(reg):
    assert reg.validate_variant("hero", None) == "standard"
    assert reg.validate_variant("hero", "aurora") == "aurora"
    with pytest.raises(ValidationError):
        reg.validate_variant("hero", "neon")


def test_slot_validation(reg):
    reg.validate_slots("hero", {"headline", "media"})
    with pytest.raises(ValidationError):
        reg.validate_slots("hero", {"headline", "confetti"})
    with pytest.raises(ValidationError):
        reg.validate_slots("hero", {"media"})  # headline required


def test_child_validation(reg):
    reg.validate_child("product_grid", "product_card")
    with pytest.raises(ValidationError):
        reg.validate_child("product_grid", "hero")
    with pytest.raises(UnknownComponentError):
        reg.validate_child("product_grid", "nope")


def test_capability_category_domain_filters(reg):
    assert {c.id for c in reg.get_by_capability("trust")} >= {
        "social_proof",
        "trust_signals",
        "reviews",
    }
    assert all(c.category == "commerce" for c in reg.get_by_category("commerce"))
    assert "product_card" not in {c.id for c in reg.get_by_domain("saas")}
    assert "hero" in {c.id for c in reg.get_by_domain("saas")}


def test_search(reg):
    assert "pricing_table" in {c.id for c in reg.search("pricing tiers")}


def test_animation_capability(reg):
    reg.validate_animation("hero", "parallax")
    with pytest.raises(ValidationError):
        reg.validate_animation("footer", "parallax")
