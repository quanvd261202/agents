"""M8: role-based motion choreography and the per-page motion budget. Deterministic, no browser."""

from __future__ import annotations

import pytest

from app.dsl import default_design_resolver
from app.dsl.choreography import BUDGET, BUDGET_GROUP, section_nodes
from app.models.common import Intensity
from app.models.dsl import AnimationIntent, SectionSpec


def motion(sections: list[tuple[str, str | None]], intensity: Intensity) -> dict[str, set[str]]:
    specs = [
        SectionSpec(
            id=f"{t}-{i}",
            type=t,
            animation=AnimationIntent(name=a, intensity=intensity) if a else None,
        )
        for i, (t, a) in enumerate(sections)
    ]
    model = default_design_resolver().preview(specs, intensity=intensity)
    return {n.id: {b.name for b in n.motion} for n in section_nodes(model.root)}


def test_a_subtle_page_gets_only_quiet_motion():
    m = motion([("hero", None), ("product_grid", None), ("stats_band", None)], Intensity.subtle)
    assert m["hero-0"] == set()  # no headline reveal, no scroll effects, no magnetic
    assert m["product_grid-1"] == {"stagger", "lift"}
    assert m["stats_band-2"] == {"stagger", "number_ticker"}


def test_a_moderate_hero_is_choreographed_as_a_whole():
    m = motion([("hero", None)], Intensity.moderate)
    assert m["hero-0"] == {"headline_reveal", "scroll_zoom", "magnetic", "tilt"}


def test_the_budget_caps_attention_grabbing_motion_and_the_earliest_sections_win():
    heads = [("hero", None), ("manifesto", None), ("editorial_quote", None), ("cta", None)]
    m = motion(heads, Intensity.moderate)
    reveals = [sid for sid, names in m.items() if "headline_reveal" in names]
    assert reveals == ["hero-0", "manifesto-1"]  # moderate allows two
    assert sum("magnetic" in names for names in m.values()) == 1


def test_expressive_pages_trade_zoom_for_parallax_and_may_stack_once():
    m = motion(
        [("image_band", None), ("image_band", None), ("manifesto", None)], Intensity.expressive
    )
    assert "parallax" in m["image_band-0"] and "scroll_zoom" not in m["image_band-0"]
    assert sum("stack" in names for names in m.values()) == 1


def test_an_explicit_pick_is_admitted_before_any_suggestion():
    # tilt is capped at one per moderate page; the Builder asked for it on the later section
    m = motion([("hero", None), ("product_spotlight", "tilt")], Intensity.moderate)
    assert "tilt" in m["product_spotlight-1"]
    assert "tilt" not in m["hero-0"]


def test_a_still_page_drops_every_behaviour_even_explicit_ones():
    m = motion([("metrics", "number_ticker"), ("product_grid", None)], Intensity.none)
    assert m == {"metrics-0": set(), "product_grid-1": set()}


@pytest.mark.parametrize("intensity", list(Intensity))
def test_no_page_ever_exceeds_its_budget(intensity):
    from app.catalog import default_component_registry

    everything = [(c.id, None) for c in default_component_registry()]
    m = motion(everything, intensity)
    for group, cap in BUDGET[intensity].items():
        used = sum(BUDGET_GROUP.get(n) == group for names in m.values() for n in names)
        assert used <= cap, (group, used, cap)
    unbudgeted = {g for g in BUDGET_GROUP.values()} - set(BUDGET[intensity])
    for group in unbudgeted:
        assert not any(BUDGET_GROUP.get(n) == group for names in m.values() for n in names)


def test_behaviour_params_come_from_the_vocabulary_presets():
    model = default_design_resolver().preview(
        [SectionSpec(id="h", type="hero")], intensity=Intensity.expressive
    )
    [hero] = section_nodes(model.root)
    reveal = next(b for b in hero.motion if b.name == "headline_reveal")
    assert reveal.params == {"distance": 120.0, "duration_ms": 1100, "stagger_ms": 80}
