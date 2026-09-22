import pytest

from app.core.exceptions import UnknownTokenError, ValidationError
from app.tokens import Theme, ThemeRegistry, TokenResolver, default_theme_registry


@pytest.fixture
def resolver() -> TokenResolver:
    return TokenResolver(default_theme_registry())


def test_theme_lookup_and_unknown():
    reg = default_theme_registry()
    assert reg.get("premium_dark").extends == "modern_dark"
    with pytest.raises(UnknownTokenError):
        reg.get("neon_brutalist")


def test_inheritance_merges_leaf_over_parent(resolver):
    t = resolver.resolve("premium_dark")
    assert t.get("color.bg") == "#050505"  # leaf
    assert t.get("color.muted") == "#a1a1aa"  # from modern_dark
    assert t.get("color.primary_fg") == "#050505"  # leaf overrides modern_light
    assert t.get("shadow.sm") == "0 1px 2px rgb(0 0 0 / 0.05)"  # from base


def test_all_seed_themes_resolve_with_every_density(resolver):
    for theme in default_theme_registry():
        for d in ("compact", "comfortable", "spacious"):
            resolver.resolve(theme.id, density=d)


def test_density_scales_spacing(resolver):
    c = resolver.resolve("modern_light", density="compact")
    s = resolver.resolve("modern_light", density="spacious")
    assert c.get("spacing.md") == "12px" and s.get("spacing.md") == "21.6px"


def test_radius_and_typography_intents(resolver):
    t = resolver.resolve("modern_light", radius="large", typography="geometric")
    assert t.get("radius.base") == "16px"
    assert "Space Grotesk" in str(t.get("typography.font_heading"))
    assert resolver.resolve("premium_light").get("radius.scale") == "large"  # theme default


def test_invalid_intents(resolver):
    with pytest.raises(ValidationError):
        resolver.resolve("modern_light", density="ultra")
    with pytest.raises(ValidationError):
        resolver.resolve("modern_light", radius="27px")
    with pytest.raises(ValidationError):
        resolver.resolve("modern_light", typography="comic")


def test_overrides_and_unknown_category(resolver):
    t = resolver.resolve("saas", overrides={"color.primary": "#ff0000"})
    assert t.get("color.primary") == "#ff0000"
    with pytest.raises(UnknownTokenError):
        resolver.resolve("saas", overrides={"padding.left": 3})


def test_responsive_values_and_css_vars(resolver):
    t = resolver.resolve("modern_light")
    assert t.get("typography.heading_size") == "2rem"  # mobile-first default
    assert t.css_variables_for("wide")["--typography-heading-size"] == "3.5rem"  # inherits desktop
    assert t.css_variables()["--color-primary"] == "#2563eb"


def test_defaults_present_and_cycle_detected():
    reg = ThemeRegistry([Theme(id="a", extends="b"), Theme(id="b", extends="a")])
    with pytest.raises(ValidationError):
        reg.chain("a")
    t = TokenResolver(default_theme_registry()).resolve("minimal")
    assert t.get("motion.duration_base") == "300ms"
    assert t.get("border.width") == "1.5px"
