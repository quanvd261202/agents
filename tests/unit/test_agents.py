"""Phase 07-10 agents against a scripted provider: no network, no API key."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.agents import ClarifierAgent, DesignBuilderAgent, DirectorAgent, PlannerAgent
from app.agents.builder import BuilderOutput
from app.animation import default_animation_registry
from app.catalog import default_component_registry
from app.core.exceptions import ValidationError
from app.core.llm import FakeLLMProvider
from app.models import (
    AnimationIntent,
    ClarifiedRequirements,
    ClarifierOutput,
    DesignDirection,
    ScreenDirection,
    ScreenPlan,
    UXPlan,
)
from app.models.common import Density, Intensity
from app.recipes import default_recipe_registry
from app.retrieval.models import RetrievedContext
from app.tokens import default_theme_registry

REQ = ClarifiedRequirements(
    product="shoe store",
    domain="ecommerce",
    target_audience="runners",
    primary_goal="sell running shoes",
    key_features=["product detail", "reviews"],
)
PLAN = UXPlan(
    product="shoe store",
    user_goals=["evaluate a shoe"],
    journey=[],
    screens=[ScreenPlan(id="detail", purpose="product evaluation", key_content=["price"])],
)
DIRECTION = DesignDirection(
    visual_style="premium_modern",
    theme="premium_light",
    typography="modern_sans",
    radius="large",
    layout_strategy="editorial_grid",
    animation="subtle_expressive",
    screens=[ScreenDirection(screen_id="detail", recipe="ecommerce_product")],
)
SCREEN = PLAN.screens[0]
CONTEXT = RetrievedContext(components=["product_detail - the buy box"], layouts=["split"])


def builder() -> DesignBuilderAgent:
    return DesignBuilderAgent(
        FakeLLMProvider(),
        default_recipe_registry(),
        default_component_registry(),
        default_animation_registry(),
    )


# --- Phase 07 ------------------------------------------------------------------------------
async def test_clarifier_returns_ready_requirements():
    llm = FakeLLMProvider([ClarifierOutput(status="ready", clarified_requirements=REQ)])
    out = await ClarifierAgent(llm, default_recipe_registry()).clarify("Build a shoe store", {})
    assert out.status == "ready"
    assert out.clarified_requirements == REQ


async def test_clarifier_prompt_forbids_designing_and_caps_questions():
    llm = FakeLLMProvider([ClarifierOutput(status="ready", clarified_requirements=REQ)])
    await ClarifierAgent(llm, default_recipe_registry(), max_questions=2).clarify(
        "Build a shoe store", {}
    )
    system = llm.calls[0][0].content
    assert "at most 2 questions" in system
    for forbidden in ("choose components", "plan screens", "invent layouts"):
        assert forbidden in system


async def test_clarifier_repairs_ready_without_requirements():
    llm = FakeLLMProvider(
        [
            ClarifierOutput(status="ready"),
            ClarifierOutput(status="ready", clarified_requirements=REQ),
        ]
    )
    out = await ClarifierAgent(llm, default_recipe_registry()).clarify("Build a shoe store", {})
    assert out.clarified_requirements == REQ
    assert len(llm.calls) == 2


async def test_clarifier_gives_up_after_two_repairs():
    llm = FakeLLMProvider([ClarifierOutput(status="ready")] * 3)
    with pytest.raises(ValidationError):
        await ClarifierAgent(llm, default_recipe_registry()).clarify("Build a shoe store", {})


async def test_clarifier_passes_existing_answers_to_the_model():
    llm = FakeLLMProvider([ClarifierOutput(status="ready", clarified_requirements=REQ)])
    await ClarifierAgent(llm, default_recipe_registry()).clarify(
        "Build a shoe store", {"audience": "runners"}
    )
    assert "runners" in llm.calls[0][1].content


# --- Phase 08 ------------------------------------------------------------------------------
async def test_planner_returns_plan_and_is_told_not_to_style():
    llm = FakeLLMProvider([PLAN])
    plan = await PlannerAgent(llm, default_recipe_registry()).plan(REQ)
    assert [s.id for s in plan.screens] == ["detail"]
    assert "MUST NOT decide: CSS" in llm.calls[0][0].content


async def test_planner_is_limited_to_page_types_the_domain_can_build():
    llm = FakeLLMProvider([PLAN])
    await PlannerAgent(llm, default_recipe_registry()).plan(REQ)
    system = llm.calls[0][0].content
    assert "cart, checkout, product_detail, product_listing, storefront." in system
    page_types = next(line for line in system.splitlines() if line.startswith("Only these kinds"))
    assert "dashboard" not in page_types


async def test_planner_rejects_duplicate_screen_ids():
    dup = PLAN.model_copy(update={"screens": [*PLAN.screens, *PLAN.screens]})
    llm = FakeLLMProvider([dup, dup, dup])
    with pytest.raises(ValidationError, match="duplicate screen ids"):
        await PlannerAgent(llm, default_recipe_registry()).plan(REQ)


# --- Phase 09 ------------------------------------------------------------------------------
def director(llm: FakeLLMProvider) -> DirectorAgent:
    return DirectorAgent(
        llm, default_theme_registry(), default_recipe_registry(), default_animation_registry()
    )


async def test_director_returns_direction():
    llm = FakeLLMProvider([DIRECTION])
    assert await director(llm).direct(REQ, PLAN) == DIRECTION


async def test_director_is_offered_only_domain_compatible_recipes():
    llm = FakeLLMProvider([DIRECTION])
    await director(llm).direct(REQ, PLAN)
    user = llm.calls[0][1].content
    assert "ecommerce_product" in user
    assert "dashboard" not in user
    assert "saas_landing" not in user  # the shop has its own storefront recipe


async def test_director_repairs_an_unknown_recipe():
    bad = DIRECTION.model_copy(
        update={"screens": [ScreenDirection(screen_id="detail", recipe="landing_page")]}
    )
    llm = FakeLLMProvider([bad, DIRECTION])
    assert await director(llm).direct(REQ, PLAN) == DIRECTION
    assert "landing_page" in llm.calls[1][-1].content


async def test_director_rejects_an_unknown_theme():
    bad = DIRECTION.model_copy(update={"theme": "neon_brutalist"})
    llm = FakeLLMProvider([bad, bad, bad])
    with pytest.raises(ValidationError, match="unknown theme"):
        await director(llm).direct(REQ, PLAN)


async def test_director_rejects_an_unknown_animation():
    bad = DIRECTION.model_copy(update={"animation": "explode"})
    llm = FakeLLMProvider([bad, bad, bad])
    with pytest.raises(ValidationError, match="unknown animation"):
        await director(llm).direct(REQ, PLAN)


# --- Phase 10 ------------------------------------------------------------------------------
VALID = BuilderOutput(
    sections=[
        {"id": "navigation", "type": "navigation", "variant": "transparent"},
        {"id": "product_detail", "type": "product_detail", "variant": "premium_split"},
        {"id": "reviews", "type": "reviews", "animation": "stagger"},
        {"id": "footer", "type": "footer"},
    ]
)


async def build_with(*responses: BuilderOutput):
    agent = builder()
    llm: FakeLLMProvider = agent._llm  # type: ignore[assignment]
    for r in responses:
        llm.push(r)
    return await agent.build(REQ, SCREEN, DIRECTION, CONTEXT), llm


async def test_builder_assembles_a_spec_the_resolver_accepts():
    from app.dsl import default_design_resolver

    spec, _ = await build_with(VALID)
    assert spec.screen_id == "detail"
    assert spec.recipe == "ecommerce_product"
    assert spec.theme == "premium_light"
    assert [s.id for s in spec.sections] == [s.id for s in VALID.sections]
    default_design_resolver().resolve(spec)  # raises if anything is unresolvable


# --- animation ownership -------------------------------------------------------------------
async def test_page_animation_comes_from_the_director_not_the_builder():
    spec, _ = await build_with(VALID)
    assert spec.animation is not None
    assert spec.animation.name == DIRECTION.animation


async def test_builder_cannot_express_a_page_level_animation():
    """The only page-motion channel is the direction, so builder/director cannot disagree."""
    assert "animation" not in BuilderOutput.model_fields
    with pytest.raises(PydanticValidationError):
        BuilderOutput.model_validate(
            {"sections": [s.model_dump() for s in VALID.sections], "animation": "parallax"}
        )


async def test_page_intensity_matches_the_resolver_alias_table():
    from app.dsl.resolver import PAGE_ANIMATION_ALIASES

    spec, _ = await build_with(VALID)
    assert spec.animation is not None
    assert spec.animation.intensity == PAGE_ANIMATION_ALIASES[DIRECTION.animation][1]


async def test_unaliased_direction_animation_falls_back_to_subtle():
    direction = DIRECTION.model_copy(update={"animation": "reveal"})
    agent = builder()
    agent._llm.push(VALID)  # type: ignore[attr-defined]
    spec = await agent.build(REQ, SCREEN, direction, CONTEXT)
    assert spec.animation == AnimationIntent(name="reveal", intensity=Intensity.subtle)


async def test_section_animation_inherits_the_page_intensity():
    spec, _ = await build_with(VALID)
    reviews = spec.find("reviews")
    assert reviews is not None and reviews.animation is not None
    assert reviews.animation.name == "stagger"  # the builder owns which
    assert reviews.animation.intensity == spec.animation.intensity  # the director owns how much


# --- derived values ------------------------------------------------------------------------
async def test_derived_values_come_from_upstream_state_only():
    spec, _ = await build_with(VALID)
    assert (spec.screen_id, spec.recipe, spec.theme, spec.visual_style, spec.density) == (
        SCREEN.id,
        "ecommerce_product",
        DIRECTION.theme,
        DIRECTION.visual_style,
        DIRECTION.density,
    )


async def test_derived_values_follow_a_changed_direction_and_plan():
    direction = DIRECTION.model_copy(
        update={
            "screens": [ScreenDirection(screen_id="home", recipe="saas_landing")],
            "theme": "modern_dark",
            "density": Density.compact,
        }
    )
    screen = ScreenPlan(id="home", purpose="discovery")
    agent = builder()
    agent._llm.push(  # type: ignore[attr-defined]
        BuilderOutput(
            sections=[
                {"id": "navigation", "type": "navigation"},
                {"id": "hero", "type": "hero"},
                {"id": "features", "type": "feature_bento"},
                {"id": "cta", "type": "cta"},
                {"id": "footer", "type": "footer"},
            ]
        )
    )
    spec = await agent.build(REQ, screen, direction, CONTEXT)
    assert (spec.screen_id, spec.recipe, spec.theme, spec.density) == (
        "home",
        "saas_landing",
        "modern_dark",
        Density.compact,
    )


async def test_builder_output_forbids_derived_fields():
    """extra='forbid' is what makes drift into upstream decisions unrepresentable."""
    for field in ("screen_id", "recipe", "theme", "visual_style", "density"):
        with pytest.raises(PydanticValidationError):
            BuilderOutput.model_validate(
                {"sections": [s.model_dump() for s in VALID.sections], field: "x"}
            )


async def test_builder_prompt_lists_slots_variants_and_retrieved_context():
    _, llm = await build_with(VALID)
    user = llm.calls[0][1].content
    assert "product_detail(variants: standard, premium_split, stacked; motion:" in user
    assert "reorderable in group 'body'" in user
    assert "product_detail - the buy box" in user
    assert "no react" in llm.calls[0][0].content.lower() or "React" in llm.calls[0][0].content


async def test_builder_fills_a_required_slot_that_has_only_one_choice():
    partial = BuilderOutput(
        sections=[s for s in VALID.sections if s.id not in ("navigation", "footer")]
    )
    spec, llm = await build_with(partial)
    assert [s.id for s in spec.sections] == ["navigation", "product_detail", "reviews", "footer"]
    assert len(llm.calls) == 1  # no repair round-trip


async def test_a_filled_slot_lands_in_recipe_order():
    partial = BuilderOutput(sections=[s for s in VALID.sections if s.id != "product_detail"])
    spec, _ = await build_with(partial)
    assert [s.id for s in spec.sections] == ["navigation", "product_detail", "reviews", "footer"]


async def test_builder_rejects_a_section_outside_the_recipe():
    bad = BuilderOutput(sections=[*VALID.sections, {"id": "pricing", "type": "pricing_table"}])
    with pytest.raises(ValidationError, match="not part of recipe"):
        await build_with(bad, bad, bad)


async def test_builder_rejects_an_unknown_variant():
    bad = BuilderOutput(
        sections=[
            s.model_copy(update={"variant": "holographic"}) if s.id == "footer" else s
            for s in VALID.sections
        ]
    )
    with pytest.raises(ValidationError):
        await build_with(bad, bad, bad)


async def test_builder_rejects_motion_the_component_cannot_do():
    bad = BuilderOutput(
        sections=[
            s.model_copy(update={"animation": "parallax"}) if s.id == "footer" else s
            for s in VALID.sections
        ]
    )
    with pytest.raises(ValidationError, match="does not support animation"):
        await build_with(bad, bad, bad)


async def test_builder_degrades_an_unsupported_entrance_instead_of_repairing():
    """`fade_up` on a grid is an intent the component cannot take literally; like the resolver
    does for the page default, it becomes the nearest entrance the component offers."""
    picked = BuilderOutput(
        sections=[
            s.model_copy(update={"animation": "fade_up"}) if s.id == "reviews" else s
            for s in VALID.sections
        ]
    )
    spec, llm = await build_with(picked)
    reviews = spec.find("reviews")
    assert reviews is not None and reviews.animation is not None
    assert reviews.animation.name == "fade_up"  # reviews supports it: kept as picked
    assert len(llm.calls) == 1

    grid = ScreenPlan(id="home", purpose="discovery")
    direction = DIRECTION.model_copy(
        update={"screens": [ScreenDirection(screen_id="home", recipe="ecommerce_home")]}
    )
    agent = builder()
    agent._llm.push(  # type: ignore[attr-defined]
        BuilderOutput(
            sections=[
                {"id": "navigation", "type": "navigation"},
                {"id": "hero", "type": "hero"},
                {"id": "featured_products", "type": "product_grid", "animation": "fade_up"},
                {"id": "footer", "type": "footer"},
            ]
        )
    )
    spec = await agent.build(REQ, grid, direction, CONTEXT)
    section = spec.find("featured_products")
    assert section is not None and section.animation is not None
    assert section.animation.name == "fade"  # the grid's nearest entrance, no repair round trip
    assert len(agent._llm.calls) == 1  # type: ignore[attr-defined]


async def test_builder_rejects_an_unknown_animation():
    bad = BuilderOutput(
        sections=[
            s.model_copy(update={"animation": "explode"}) if s.id == "reviews" else s
            for s in VALID.sections
        ]
    )
    with pytest.raises(ValidationError, match="unknown animation"):
        await build_with(bad, bad, bad)


async def test_builder_rejects_sections_reordered_out_of_their_group():
    bad = BuilderOutput(
        sections=[VALID.sections[2], VALID.sections[0], VALID.sections[1], VALID.sections[3]]
    )
    with pytest.raises(ValidationError):
        await build_with(bad, bad, bad)


# --- wiring --------------------------------------------------------------------------------
async def test_bootstrap_wires_the_agent_chain_end_to_end():
    """Phases 07-10 wired as they run in production, on the fake provider and offline embeddings."""
    from app.bootstrap import build_services
    from app.core.config import Settings

    settings = Settings(
        llm_provider="fake",
        embedding_provider="hashing",
        image_provider="fake",
        persistence="memory",
        _env_file=None,
    )
    svc = await build_services(settings)
    llm: FakeLLMProvider = svc.llm  # type: ignore[assignment]
    for response in (
        ClarifierOutput(status="ready", clarified_requirements=REQ),
        PLAN,
        DIRECTION,
        VALID,
    ):
        llm.push(response)

    clarified = await svc.clarifier.clarify("Sell running shoes online", {})
    assert clarified.clarified_requirements is not None
    plan = await svc.planner.plan(clarified.clarified_requirements)
    direction = await svc.director.direct(clarified.clarified_requirements, plan)
    screen = plan.screens[0]
    context = await svc.retrieval.retrieve(
        clarified.clarified_requirements, direction, direction.recipe_for(screen.id)
    )
    assert context.components
    spec = await svc.builder.build(clarified.clarified_requirements, screen, direction, context)
    model = svc.resolver.resolve(spec)
    assert model.screen_id == "detail"
    assert model.root.children


async def test_clarifier_may_not_ask_again_once_answers_exist():
    asking = ClarifierOutput(status="needs_clarification", questions=[{"question": "Who?"}])
    llm = FakeLLMProvider([asking, ClarifierOutput(status="ready", clarified_requirements=REQ)])
    out = await ClarifierAgent(llm, default_recipe_registry()).clarify(
        "Build a shoe store", {"Who?": "runners"}
    )
    assert out.status == "ready"
    assert "already answered" in llm.calls[1][-1].content


async def test_clarifier_may_ask_on_the_first_pass():
    asking = ClarifierOutput(status="needs_clarification", questions=[{"question": "Who?"}])
    out = await ClarifierAgent(FakeLLMProvider([asking]), default_recipe_registry()).clarify(
        "Build a shoe store", {}
    )
    assert out.status == "needs_clarification"


async def test_clarifier_rejects_a_domain_outside_the_recipe_vocabulary():
    bad = ClarifierOutput(
        status="ready", clarified_requirements=REQ.model_copy(update={"domain": "E-commerce"})
    )
    llm = FakeLLMProvider([bad, ClarifierOutput(status="ready", clarified_requirements=REQ)])
    out = await ClarifierAgent(llm, default_recipe_registry()).clarify("A coffee shop", {})
    assert out.clarified_requirements is not None
    assert out.clarified_requirements.domain == "ecommerce"
    assert "must be one of" in llm.calls[1][-1].content


async def test_clarifier_prompt_lists_the_allowed_domains():
    llm = FakeLLMProvider([ClarifierOutput(status="ready", clarified_requirements=REQ)])
    await ClarifierAgent(llm, default_recipe_registry()).clarify("A coffee shop", {})
    assert "admin, dashboard, ecommerce, saas" in llm.calls[0][0].content


# --- every planned screen --------------------------------------------------------------------
SHOP_PLAN = UXPlan(
    product="shoe store",
    user_goals=["buy shoes"],
    journey=[],
    screens=[
        ScreenPlan(id="home", purpose="discovery"),
        ScreenPlan(id="listing", purpose="product discovery"),
        ScreenPlan(id="detail", purpose="product evaluation"),
        ScreenPlan(id="cart", purpose="purchase preparation"),
        ScreenPlan(id="checkout", purpose="purchase"),
    ],
)
SHOP_DIRECTION = DIRECTION.model_copy(
    update={
        "screens": [
            ScreenDirection(screen_id=s, recipe=f"ecommerce_{r}")
            for s, r in [
                ("home", "home"),
                ("listing", "listing"),
                ("detail", "product"),
                ("cart", "cart"),
                ("checkout", "checkout"),
            ]
        ]
    }
)


async def test_director_assigns_a_recipe_to_every_planned_screen():
    llm = FakeLLMProvider([SHOP_DIRECTION])
    d = await director(llm).direct(REQ, SHOP_PLAN)
    assert [d.recipe_for(s.id) for s in SHOP_PLAN.screens] == [
        "ecommerce_home",
        "ecommerce_listing",
        "ecommerce_product",
        "ecommerce_cart",
        "ecommerce_checkout",
    ]


async def test_director_is_shown_each_recipe_page_type():
    llm = FakeLLMProvider([SHOP_DIRECTION])
    await director(llm).direct(REQ, SHOP_PLAN)
    user = llm.calls[0][1].content
    assert "- ecommerce_cart (cart):" in user
    assert "- ecommerce_checkout (checkout):" in user


async def test_director_repairs_a_screen_it_left_out():
    missing = SHOP_DIRECTION.model_copy(update={"screens": SHOP_DIRECTION.screens[:-1]})
    llm = FakeLLMProvider([missing, SHOP_DIRECTION])
    assert await director(llm).direct(REQ, SHOP_PLAN) == SHOP_DIRECTION
    assert "exactly once" in llm.calls[1][-1].content


async def test_director_rejects_a_screen_assigned_twice():
    twice = SHOP_DIRECTION.model_copy(
        update={"screens": [*SHOP_DIRECTION.screens, SHOP_DIRECTION.screens[0]]}
    )
    llm = FakeLLMProvider([twice, twice, twice])
    with pytest.raises(ValidationError, match="exactly once"):
        await director(llm).direct(REQ, SHOP_PLAN)


async def test_builder_composes_the_given_screen_from_its_own_recipe():
    cart = SHOP_PLAN.screens[3]
    agent = builder()
    llm: FakeLLMProvider = agent._llm  # type: ignore[assignment]
    llm.push(
        BuilderOutput(
            sections=[
                {"id": "navigation", "type": "navigation"},
                {"id": "cart_items", "type": "cart_items"},
                {"id": "order_summary", "type": "order_summary"},
                {"id": "footer", "type": "footer"},
            ]
        )
    )
    spec = await agent.build(REQ, cart, SHOP_DIRECTION, CONTEXT)
    assert (spec.screen_id, spec.recipe) == ("cart", "ecommerce_cart")
    assert "Recipe `ecommerce_cart`" in llm.calls[0][1].content
    assert "Screen: cart - purchase preparation" in llm.calls[0][1].content


# --- the user's brief reaches the agents that shape the product ----------------------------
BRIEF = "Homepage: large editorial hero, featured collections Coffee, Tea, Cold Drinks."


async def test_planner_sees_the_brief_verbatim_and_treats_it_as_the_source_of_truth():
    llm = FakeLLMProvider([PLAN])
    await PlannerAgent(llm, default_recipe_registry()).plan(REQ, BRIEF)
    assert f"The user's brief, verbatim:\n{BRIEF}" in llm.calls[0][1].content
    assert "source of truth" in llm.calls[0][0].content


async def test_director_sees_the_brief_for_brand_direction():
    llm = FakeLLMProvider([DIRECTION])
    await director(llm).direct(REQ, PLAN, BRIEF)
    assert BRIEF in llm.calls[0][1].content


async def test_no_brief_adds_no_brief_block():
    llm = FakeLLMProvider([PLAN])
    await PlannerAgent(llm, default_recipe_registry()).plan(REQ)
    assert "brief, verbatim" not in llm.calls[0][1].content


# --- brand axes ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("field", "value"),
    [("palette", "neon"), ("typography", "comic_sans"), ("radius", "blobby")],
)
async def test_director_rejects_brand_values_outside_the_registries(field, value):
    bad = DIRECTION.model_copy(update={field: value})
    with pytest.raises(ValidationError, match=f"unknown {field}"):
        await director(FakeLLMProvider([bad, bad, bad])).direct(REQ, PLAN)


async def test_director_is_shown_palettes_and_typography_with_their_moods():
    llm = FakeLLMProvider([DIRECTION])
    await director(llm).direct(REQ, PLAN)
    user = llm.calls[0][1].content
    assert "- espresso (light) - coffee, warm" in user
    assert "- editorial_serif - editorial, warm" in user


async def test_the_chosen_palette_reaches_the_spec():
    agent = builder()
    agent._llm.push(VALID)  # type: ignore[attr-defined]
    spec = await agent.build(
        REQ, SCREEN, DIRECTION.model_copy(update={"palette": "espresso"}), CONTEXT
    )
    assert (spec.palette, spec.typography, spec.radius) == ("espresso", "modern_sans", "large")
