"""M10 Copywriter against a scripted provider: no network, no API key."""

from __future__ import annotations

import pytest

from app.agents import CopywriterAgent
from app.agents.copywriter import CopyOutput, item_count
from app.catalog import default_component_registry
from app.core.exceptions import ValidationError
from app.core.llm import FakeLLMProvider
from app.dsl import default_design_resolver
from app.models import (
    ClarifiedRequirements,
    DesignDirection,
    DesignSpec,
    ScreenDirection,
    ScreenPlan,
)

REQ = ClarifiedRequirements(
    product="Ember & Leaf",
    domain="ecommerce",
    target_audience="home baristas",
    primary_goal="sell coffee beans",
    key_features=["subscriptions"],
    brand_notes="warm, unhurried",
)
SCREEN = ScreenPlan(id="home", purpose="discovery", key_content=["featured beans", "brand story"])
DIRECTION = DesignDirection(
    visual_style="warm_editorial",
    theme="premium_light",
    typography="editorial_serif",
    radius="large",
    layout_strategy="editorial_grid",
    animation="subtle",
    screens=[ScreenDirection(screen_id="home", recipe="ecommerce_home")],
)
SPEC = DesignSpec(
    screen_id="home",
    recipe="ecommerce_home",
    visual_style="warm_editorial",
    theme="premium_light",
    sections=[
        {"id": "navigation", "type": "navigation"},
        {"id": "hero", "type": "hero"},
        {"id": "featured_products", "type": "product_grid", "variant": "premium"},
        {"id": "cta", "type": "cta"},
        {"id": "footer", "type": "footer"},
    ],
)
ITEMS = [
    {
        "title": f"Roast No. {i}",
        "note": "Chocolate, cherry, a long finish",
        "price": "$18",
        "badge": "New" if i == 1 else None,
        "image": "bag of roasted coffee beans on oak",
    }
    for i in range(1, 7)
]
WRITTEN = CopyOutput(
    sections=[
        {
            "id": "hero",
            "slots": [
                {"slot": "headline", "text": "Coffee worth waking for"},
                {"slot": "subhead", "text": "Roasted weekly, shipped the same day."},
                {"slot": "media", "text": "pour-over coffee on a sunlit oak counter"},
            ],
        },
        {
            "id": "featured_products",
            "slots": [{"slot": "title", "text": "This week's roasts"}],
            "items": ITEMS,
        },
    ]
)


async def write(*responses: CopyOutput, spec: DesignSpec = SPEC, brief: str = ""):
    llm = FakeLLMProvider(list(responses))
    agent = CopywriterAgent(llm, default_component_registry())
    return await agent.write(REQ, SCREEN, DIRECTION, spec, brief), llm


# --- copy lands in the spec ------------------------------------------------------------------
async def test_copy_lands_in_content_and_items_become_product_cards():
    spec, _ = await write(WRITTEN)
    hero = spec.find("hero")
    assert hero is not None
    assert hero.content["headline"] == "Coffee worth waking for"
    assert hero.content["media"] == "pour-over coffee on a sunlit oak counter"

    grid = spec.find("featured_products")
    assert grid is not None
    assert grid.content == {"title": "This week's roasts"}
    assert [c.id for c in grid.children] == [f"featured_products-item-{i}" for i in range(1, 7)]
    first = grid.children[0]
    assert first.type == "product_card"
    assert first.variant == "premium"  # follows the grid's variant
    assert first.content == {
        "image": "bag of roasted coffee beans on oak",
        "title": "Roast No. 1",
        "price": "$18",
        "note": "Chocolate, cherry, a long finish",
        "badge": "New",
    }
    assert "badge" not in grid.children[1].content  # optional, omitted rather than blank
    default_design_resolver().resolve(spec)  # raises if anything is unresolvable


async def test_sections_the_writer_skipped_are_untouched():
    spec, _ = await write(WRITTEN)
    for sid in ("navigation", "cta", "footer"):
        section = spec.find(sid)
        assert section is not None
        assert section.content == {} and section.children == []
    assert [s.id for s in spec.sections] == [s.id for s in SPEC.sections]  # structure kept


async def test_blank_texts_are_dropped():
    out = CopyOutput(sections=[{"id": "hero", "slots": [{"slot": "headline", "text": "   "}]}])
    spec, _ = await write(out)
    assert spec.find("hero").content == {}  # type: ignore[union-attr]


async def test_item_counts_follow_what_the_component_shows():
    assert item_count("product_grid", None) == 6
    assert item_count("product_grid", "dense") == 8
    assert item_count("related_products", "grid") == 4
    assert item_count("related_products", "carousel") == 6
    assert item_count("cart_items", None) == 3


# --- prompt ----------------------------------------------------------------------------------
async def test_prompt_lists_slots_with_formats_and_item_counts():
    _, llm = await write(WRITTEN)
    system, user = llm.calls[0][0].content, llm.calls[0][1].content
    assert "MUST NOT change structure" in system
    assert "lorem ipsum" in system
    assert "Product: Ember & Leaf (ecommerce), for home baristas" in user
    assert "Brand notes: warm, unhurried" in user
    assert "Key content: featured beans, brand story" in user
    assert "- hero (hero, variant" in user
    assert "media (the photograph to show" in user
    assert (
        "- featured_products (product_grid, variant premium): eyebrow, title, subtitle, cta; "
        "items: 6 product cards" in user
    )
    assert "- footer (footer, variant" in user


async def test_the_brief_reaches_the_copywriter_verbatim():
    brief = "Homepage: feature the Ember Roast and the Sunday Blend."
    _, llm = await write(WRITTEN, brief=brief)
    assert f"The user's brief, verbatim:\n{brief}" in llm.calls[0][1].content
    _, llm = await write(WRITTEN)
    assert "brief, verbatim" not in llm.calls[0][1].content


# --- validation and repair -------------------------------------------------------------------
async def test_an_unknown_slot_is_repaired():
    bad = CopyOutput(sections=[{"id": "hero", "slots": [{"slot": "tagline", "text": "x"}]}])
    spec, llm = await write(bad, WRITTEN)
    assert spec.find("hero").content["headline"] == "Coffee worth waking for"  # type: ignore[union-attr]
    assert len(llm.calls) == 2
    assert "hero has no slot ['tagline']" in llm.calls[1][-1].content


async def test_an_unknown_section_is_rejected():
    bad = CopyOutput(sections=[{"id": "pricing", "slots": [{"slot": "title", "text": "x"}]}])
    with pytest.raises(ValidationError, match="not a section of this screen"):
        await write(bad, bad, bad)


async def test_items_on_a_component_without_products_are_rejected():
    bad = CopyOutput(sections=[{"id": "cta", "items": ITEMS[:1]}])
    with pytest.raises(ValidationError, match="does not list products"):
        await write(bad, bad, bad)


async def test_a_section_written_twice_is_rejected():
    twice = CopyOutput(sections=[*WRITTEN.sections, WRITTEN.sections[0]])
    with pytest.raises(ValidationError, match="appears twice"):
        await write(twice, twice, twice)


@pytest.mark.parametrize("text", ["Lorem ipsum dolor sit amet", "Product 1", "Welcome to [brand]"])
async def test_placeholder_copy_is_rejected(text):
    bad = CopyOutput(sections=[{"id": "hero", "slots": [{"slot": "headline", "text": text}]}])
    with pytest.raises(ValidationError, match="placeholder copy"):
        await write(bad, bad, bad)


async def test_output_cannot_carry_structure():
    """extra='forbid' keeps the writer to words: no types, variants or layouts are representable."""
    from pydantic import ValidationError as PydanticValidationError

    for field in ("type", "variant", "layout", "animation"):
        with pytest.raises(PydanticValidationError):
            CopyOutput.model_validate({"sections": [{"id": "hero", field: "split"}]})
