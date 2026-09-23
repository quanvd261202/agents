import pytest

from app.animation import AnimationResolver, default_animation_registry
from app.core.exceptions import UnknownAnimationError, ValidationError
from app.models.dsl import AnimationIntent


@pytest.fixture
def res() -> AnimationResolver:
    return AnimationResolver(default_animation_registry())


def test_vocabulary_complete():
    ids = set(default_animation_registry().ids())
    assert {
        "fade",
        "fade_up",
        "fade_down",
        "scale",
        "reveal",
        "stagger",
        "slide",
        "parallax",
        "float",
        "glow",
        "marquee",
        "magnetic",
        "morph",
        "number_ticker",
    } <= ids


def test_semantic_intent_to_motion_config(res):
    r = res.resolve(AnimationIntent(name="fade_up", intensity="subtle"), child_count=1)
    assert r.engine == "motion"
    assert r.config["initial"] == {"opacity": 0, "y": 12}
    assert r.config["transition"]["duration"] == 0.35
    assert "stagger" not in r.config


def test_intensity_scales_and_stagger_applies_with_children(res):
    sub = res.resolve(AnimationIntent(name="stagger", intensity="subtle"), child_count=4)
    exp = res.resolve(AnimationIntent(name="stagger", intensity="expressive"), child_count=4)
    assert sub.config["stagger"]["staggerChildren"] < exp.config["stagger"]["staggerChildren"]
    assert exp.config["initial"]["filter"].startswith("blur")
    assert res.resolve(AnimationIntent(name="fade", intensity="none")).config == {}


def test_reduced_motion(res):
    assert res.resolve(AnimationIntent(name="fade_up")).reduced_motion_config["animate"] == {
        "opacity": 1
    }
    assert res.resolve(AnimationIntent(name="parallax")).reduced_motion_config == {"disabled": True}
    assert res.resolve(AnimationIntent(name="marquee")).reduced_motion_config["static"] is True
    assert (
        res.resolve(AnimationIntent(name="number_ticker")).reduced_motion_config["component"]
        == "StaticNumber"
    )


def test_unknown_and_disallowed(res):
    with pytest.raises(UnknownAnimationError):
        res.resolve(AnimationIntent(name="explode"))
    with pytest.raises(ValidationError):
        res.resolve(AnimationIntent(name="parallax"), allowed=["fade", "none"])
    assert res.resolve(AnimationIntent(name="none"), allowed=["fade"]).config == {}


def test_all_definitions_compile_for_all_intensities(res):
    for d in default_animation_registry():
        for i in ("none", "subtle", "moderate", "expressive"):
            res.resolve(AnimationIntent(name=d.id, intensity=i), child_count=3)


def test_reveal_clips_via_keyframes_and_never_via_initial():
    """A clip-path in `initial` stalls the whole entrance in the browser, opacity included, so the
    section stays invisible. Keyframes on `animate` are the only form that plays."""
    from app.animation import AnimationResolver, default_animation_registry
    from app.models.common import Intensity
    from app.models.dsl import AnimationIntent

    resolved = AnimationResolver(default_animation_registry()).resolve(
        AnimationIntent(name="reveal", intensity=Intensity.moderate)
    )
    assert resolved is not None
    assert "clipPath" not in resolved.config["initial"]
    assert resolved.config["initial"]["opacity"] == 0.0  # what hides it until the entrance runs
    assert resolved.config["animate"]["clipPath"] == [
        "inset(0% 0% 100% 0%)",
        "inset(0% 0% 0% 0%)",
    ]
