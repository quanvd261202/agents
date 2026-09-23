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
    assert t.get("shadow.sm") == "0 1px 2px 0px rgb(0 0 0 / 0.21)"  # stronger on a dark bg


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


# --- tokens v2: palettes, fluid type, radius roles ----------------------------------------
def test_every_palette_meets_wcag_aa_for_every_checked_pair():
    from app.tokens.palettes import CONTRAST_PAIRS, contrast, default_palette_registry

    for p in default_palette_registry():
        for fg, bg, need in CONTRAST_PAIRS:
            assert contrast(p.colors[fg], p.colors[bg]) >= need, (p.id, fg, bg)


def test_an_unreadable_palette_cannot_be_built():
    from pydantic import ValidationError as PydanticError

    from app.tokens.palettes import PALETTES, Palette

    good = PALETTES[0].model_dump()
    with pytest.raises(PydanticError, match="fails WCAG AA"):
        Palette.model_validate({**good, "colors": {**good["colors"], "muted": "#dddddd"}})


def test_a_palette_replaces_the_theme_colours_and_tints_shadows(resolver):
    t = resolver.resolve("modern_light", palette="espresso")
    assert t.get("color.bg") == "#f7f1e8"
    assert t.get("color.media_a") == "#c9a27e"  # roles the theme never had
    assert "59 37 24" in str(t.get("shadow.md"))


def test_type_scale_is_fluid_from_phone_to_desktop(resolver):
    from app.tokens.resolver import fluid_size

    t = resolver.resolve("modern_light", typography="editorial_serif")
    assert t.get("typography.size_body") == "1rem"
    assert str(t.get("typography.size_display")).startswith("clamp(")
    # a larger ratio means a more dramatic desktop headline; phones stay the same size
    tight, loud = fluid_size(6, 1.25), fluid_size(6, 1.5)
    assert tight.split(",")[0] == loud.split(",")[0]
    assert float(loud.rsplit(" ", 1)[-1].rstrip("rem)")) > float(
        tight.rsplit(" ", 1)[-1].rstrip("rem)")
    )


def test_radius_roles_share_one_personality(resolver):
    soft = resolver.resolve("modern_light", radius="large")
    assert (soft.get("radius.card"), soft.get("radius.lg"), soft.get("radius.button")) == (
        "16px",
        "24px",
        "16px",
    )
    assert resolver.resolve("modern_light", radius="full").get("radius.button") == "9999px"
    assert resolver.resolve("modern_light", radius="none").get("radius.media") == "0px"


def test_brand_axes_on_a_spec_reach_the_rendered_css():
    from app.dsl import default_design_resolver
    from app.models import DesignSpec
    from tests.fixtures.specs import ALL

    spec = DesignSpec.model_validate(
        {
            **ALL["ecommerce_home"],
            "palette": "matcha",
            "typography": "grotesk_display",
            "radius": "full",
        }
    )
    css = default_design_resolver().resolve(spec).css_variables
    assert css["--color-primary"] == "#2f4a2a"
    assert "Bricolage" in css["--typography-font-heading"]
    assert css["--radius-button"] == "9999px"


def test_every_theme_without_a_palette_meets_the_same_contrast_rule(resolver):
    """A spec may name a theme and no palette; its colours must be as readable as a palette's
    and define every role the components use."""
    from app.tokens.palettes import CONTRAST_PAIRS, ROLES, contrast

    failures = []
    for theme in default_theme_registry():
        if theme.id == "base":
            continue
        colors = {
            k.removeprefix("color."): str(v)
            for k, v in resolver.resolve(theme.id).values.items()
            if k.startswith("color.")
        }
        missing = [r for r in ROLES if r not in colors]
        if missing:
            failures.append(f"{theme.id}: missing {missing}")
            continue
        for fg, bg, need in CONTRAST_PAIRS:
            ratio = contrast(colors[fg], colors[bg])
            if ratio < need:
                failures.append(f"{theme.id}: {fg}/{bg} {ratio:.2f} < {need}")
    assert not failures, failures
