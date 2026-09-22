import pytest
from pydantic import ValidationError as PydanticError

from app.core.exceptions import UnknownLayoutError, ValidationError
from app.layout import LayoutResolver, LayoutSpec, LayoutType, default_layout_registry


@pytest.fixture
def res() -> LayoutResolver:
    return LayoutResolver(default_layout_registry())


def test_split_ratio_and_mobile_stack(res):
    r = res.resolve(LayoutSpec(type="split", ratio="40/60", gap="xl"), child_count=2)
    assert r.props["gridTemplateColumns"] == "40fr 60fr"
    assert r.props["gap"] == "var(--spacing-xl)"
    assert r.responsive["mobile"]["gridTemplateColumns"] == "1fr"


def test_grid_defaults_and_responsive_columns(res):
    r = res.resolve(LayoutSpec(type="grid"), child_count=6)
    assert r.props["columns"] == 3
    assert r.responsive["mobile"]["columns"] == 1 and r.responsive["tablet"]["columns"] == 2
    r2 = res.resolve(
        LayoutSpec(type="grid", columns=4, responsive={"wide": {"columns": 5}}), child_count=8
    )
    assert r2.responsive["wide"]["columns"] == 5


def test_sidebar_position_and_hide_secondary(res):
    r = res.resolve(LayoutSpec(type="sidebar", sidebar_position="right"), child_count=2)
    assert r.props["gridTemplateColumns"] == "75fr 25fr"
    assert r.responsive["mobile"]["secondaryHidden"] is True


def test_invalid_ratio_and_columns_rejected_at_parse():
    with pytest.raises(PydanticError):
        LayoutSpec(type="split", ratio="45/55")
    with pytest.raises(PydanticError):
        LayoutSpec(type="grid", columns=9)


def test_unsupported_properties(res):
    with pytest.raises(ValidationError):
        res.resolve(LayoutSpec(type="stack", columns=2))
    with pytest.raises(ValidationError):
        res.resolve(LayoutSpec(type="grid", ratio="50/50"))
    with pytest.raises(ValidationError):
        res.resolve(LayoutSpec(type="grid", responsive={"mobile": {"collapse": "hide_secondary"}}))


def test_impossible_nesting(res):
    with pytest.raises(ValidationError):
        res.resolve(LayoutSpec(type="sidebar"), child_count=2, parent=LayoutType.sidebar)
    with pytest.raises(ValidationError):
        res.resolve(LayoutSpec(type="full_bleed"), child_count=1, parent=LayoutType.container)
    res.resolve(LayoutSpec(type="grid"), child_count=3, parent=LayoutType.container)  # fine


def test_child_count_bounds(res):
    with pytest.raises(ValidationError):
        res.resolve(LayoutSpec(type="split"), child_count=1)
    with pytest.raises(ValidationError):
        res.resolve(LayoutSpec(type="centered"), child_count=2)
    with pytest.raises(ValidationError):
        res.resolve(LayoutSpec(type="bento"), child_count=2)


def test_unknown_layout():
    with pytest.raises(UnknownLayoutError):
        default_layout_registry().get("absolute")
