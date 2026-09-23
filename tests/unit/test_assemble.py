"""M13 step 4: the site assembled from the screens, the runtime seed, plan repair by patches
(rules first, the model second), and the fan-in in the graph."""

from __future__ import annotations

import pytest

from app.agents import FlowFixerAgent
from app.catalog import default_component_registry
from app.core.exceptions import ValidationError
from app.core.llm import FakeLLMProvider
from app.dsl import default_design_resolver
from app.flow import (
    apply_patches,
    assemble_site,
    default_intent_registry,
    default_runtime_state,
    rule_patches,
)
from app.graph.builder import build_graph
from app.graph.summary import summarize
from app.models import (
    Collection,
    ContentItem,
    ContentModel,
    DeadControl,
    DesignDirection,
    DesignSpec,
    FlowFixResult,
    FlowReport,
    FlowStep,
    ImageRef,
    ItemBinding,
    JourneyStep,
    Link,
    ScreenDirection,
    ScreenPlan,
    SiteMap,
    SitePlanPatch,
    UXPlan,
)
from app.recipes import default_recipe_registry
from tests.conftest import StubServices, make_services

INTENTS = default_intent_registry()
RECIPES = default_recipe_registry()
COMPONENTS = default_component_registry()

PLAN = UXPlan(
    product="shop",
    user_goals=["buy"],
    journey=[
        JourneyStep(screen="home", intent="browse", to="listing"),
        JourneyStep(screen="listing", intent="open_item", to="detail"),
    ],
    screens=[
        ScreenPlan(
            id="home",
            purpose="d",
            route="/",
            nav_label="Home",
            links=[Link(intent="browse", to="listing")],
        ),
        ScreenPlan(
            id="listing",
            purpose="b",
            route="/shop",
            nav_label="Shop",
            links=[Link(intent="open_item", to="detail")],
        ),
        ScreenPlan(id="detail", purpose="e", route="/products/:id"),
        ScreenPlan(id="cart", purpose="c", route="/cart"),
    ],
)
DIRECTION = DesignDirection(
    visual_style="warm",
    theme="premium_light",
    typography="modern_sans",
    radius="large",
    layout_strategy="grid",
    animation="subtle",
    screens=[
        ScreenDirection(screen_id="home", recipe="ecommerce_home"),
        ScreenDirection(screen_id="listing", recipe="ecommerce_listing"),
        ScreenDirection(screen_id="detail", recipe="ecommerce_product"),
        ScreenDirection(screen_id="cart", recipe="ecommerce_cart"),
    ],
)
CONTENT = ContentModel(
    brand="Ember & Leaf",
    collections=[
        Collection(
            id="products",
            item_label="coffee",
            items=[
                ContentItem(
                    id=f"roast-{i}", title=f"Roast {i}", price="$18", image="beans", tags=["medium"]
                )
                for i in range(1, 5)
            ],
        )
    ],
)


def home_spec() -> DesignSpec:
    card = {
        "id": "featured_products-item-1",
        "type": "product_card",
        "content": {"image": "beans", "title": "Roast 1", "price": "$18"},
        "binding": ItemBinding(collection="products", item="roast-1"),
        "images": {"image": [ImageRef(url="https://img/roast-1.jpg")]},
    }
    return DesignSpec(
        screen_id="home",
        recipe="ecommerce_home",
        visual_style="warm",
        theme="premium_light",
        sections=[
            {"id": "navigation", "type": "navigation"},
            {"id": "hero", "type": "hero"},
            {"id": "featured_products", "type": "product_grid", "children": [card]},
            {"id": "footer", "type": "footer"},
        ],
    )


# --- assemble ------------------------------------------------------------------------------------
def test_assemble_keys_screens_by_id_and_learns_item_photographs():
    site_map = SiteMap.from_plan(PLAN)
    model = default_design_resolver().resolve(home_spec(), site=site_map)
    site = assemble_site(PLAN, CONTENT, {"home": model})
    assert list(site.screens) == ["home"]
    assert site.screens["home"].route == "/"
    assert site.site.entry == "home"
    items = {i.id: i for i in site.content.collections[0].items}
    assert items["roast-1"].image_url == "https://img/roast-1.jpg"
    assert items["roast-2"].image_url is None
    # the content model in state is untouched
    assert CONTENT.collections[0].items[0].image_url is None


def test_the_seeded_state_puts_two_items_in_the_cart_and_nothing_else():
    state = default_runtime_state(CONTENT)
    assert [(line.item, line.qty) for line in state.cart] == [("roast-1", 1), ("roast-2", 2)]
    assert state.filters == [] and state.query == ""
    assert default_runtime_state(None).cart == []
    assert default_runtime_state(ContentModel(brand="X")).cart == []


# --- patches -------------------------------------------------------------------------------------
def test_patches_apply_to_a_copy_and_the_result_is_validated():
    patched = apply_patches(
        PLAN,
        [
            SitePlanPatch(op="add_edge", screen="detail", intent="add_to_cart", to="cart"),
            SitePlanPatch(op="set_route", screen="cart", route="/bag"),
            SitePlanPatch(op="retarget_edge", screen="home", intent="browse", to="listing"),
        ],
        INTENTS,
        DIRECTION,
        RECIPES,
    )
    assert patched.screen("detail").links == [Link(intent="add_to_cart", to="cart")]
    assert patched.screen("cart").route == "/bag"
    assert PLAN.screen("detail").links == [] and PLAN.screen("cart").route == "/cart"


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        (
            SitePlanPatch(op="add_edge", screen="nowhere", intent="browse", to="listing"),
            "no screen",
        ),
        (
            SitePlanPatch(op="add_edge", screen="home", intent="teleport", to="listing"),
            "unknown intent",
        ),
        (
            SitePlanPatch(op="add_edge", screen="home", intent="view_cart", to="listing"),
            "needs a cart recipe",
        ),
        (
            SitePlanPatch(op="retarget_edge", screen="cart", intent="checkout", to="home"),
            "no checkout link",
        ),
        (SitePlanPatch(op="set_route", screen="cart", route="/"), "used by both"),
        (SitePlanPatch(op="set_route", screen="detail", route="/product"), "needs one :id segment"),
        (SitePlanPatch(op="add_edge", screen="home", intent="browse"), "needs intent and to"),
    ],
)
def test_a_patch_that_does_not_hold_up_is_refused_with_the_reason(patch, message):
    with pytest.raises(ValidationError, match=message):
        apply_patches(PLAN, [patch], INTENTS, DIRECTION, RECIPES)


def test_rules_add_the_edge_a_dead_control_wants_when_the_plan_has_that_page():
    report = FlowReport(
        steps=[],
        dead=[
            DeadControl(screen="detail", role="primary_cta", section="product_detail", text="Add"),
            DeadControl(screen="home", role="cart", section="navigation"),
            DeadControl(screen="home", role="secondary_cta", section="hero", text="Our story"),
        ],
    )
    patches = rule_patches(PLAN, report, DIRECTION, RECIPES, COMPONENTS, INTENTS)
    assert patches == [
        SitePlanPatch(op="add_edge", screen="detail", intent="add_to_cart", to="cart"),
        SitePlanPatch(op="add_edge", screen="home", intent="view_cart", to="cart"),
    ]  # learn_more has no page type: left to the model


def test_rules_add_a_journey_steps_missing_link_and_never_a_screen():
    plan = PLAN.model_copy(
        update={
            "journey": [
                *PLAN.journey,
                JourneyStep(screen="detail", intent="add_to_cart", to="cart"),
            ]
        }
    )
    report = FlowReport(
        steps=[
            FlowStep(
                screen="detail", intent="add_to_cart", to="cart", ok=False, detail="no control"
            ),
            FlowStep(screen="home", intent="checkout", to="checkout", ok=False, detail="not built"),
        ]
    )
    patches = rule_patches(plan, report, DIRECTION, RECIPES, COMPONENTS, INTENTS)
    assert patches == [
        SitePlanPatch(op="add_edge", screen="detail", intent="add_to_cart", to="cart")
    ]


# --- flow fixer agent ----------------------------------------------------------------------------
def fixer(*responses) -> FlowFixerAgent:
    return FlowFixerAgent(FakeLLMProvider(list(responses)), RECIPES, COMPONENTS)


async def test_the_fixer_uses_rules_without_a_model_call():
    report = FlowReport(dead=[DeadControl(screen="home", role="cart", section="navigation")])
    agent = fixer()
    fix = await agent.fix(PLAN, report, DIRECTION)
    assert fix.status == "success" and fix.source == "rule"
    assert agent.apply(PLAN, fix).screen("home").links == [
        Link(intent="browse", to="listing"),
        Link(intent="view_cart", to="cart"),
    ]
    assert agent._llm.calls == []  # type: ignore[attr-defined]


async def test_the_model_proposes_patches_and_a_bad_one_is_handed_back():
    from app.agents.flow_fixer import FlowFixerOutput

    report = FlowReport(dead=[DeadControl(screen="home", role="secondary_cta", section="hero")])
    bad = FlowFixerOutput(
        status="success",
        patches=[SitePlanPatch(op="add_edge", screen="home", intent="learn_more", to="nowhere")],
        reason=None,
    )
    good = FlowFixerOutput(
        status="success",
        patches=[SitePlanPatch(op="add_edge", screen="home", intent="learn_more", to="detail")],
        reason=None,
    )
    agent = fixer(bad, good)
    fix = await agent.fix(PLAN, report, DIRECTION)
    assert fix.source == "model" and fix.patches == good.patches
    llm: FakeLLMProvider = agent._llm  # type: ignore[assignment]
    assert "not a planned screen" in llm.calls[1][-1].content
    assert "cannot add" in llm.calls[0][0].content


async def test_the_model_may_decline_when_a_screen_is_missing():
    from app.agents.flow_fixer import FlowFixerOutput

    report = FlowReport(
        steps=[FlowStep(screen="cart", intent="checkout", to="checkout", ok=False, detail="x")]
    )
    plan = PLAN.model_copy(update={"journey": []})
    out = FlowFixerOutput(status="failure", patches=[], reason="no checkout screen")
    fix = await fixer(out).fix(plan, report, DIRECTION)
    assert fix.status == "failure" and fix.reason == "no checkout screen"


# --- graph fan-in --------------------------------------------------------------------------------
async def test_the_graph_assembles_once_after_every_screen_and_walks_the_journeys():
    stub = StubServices(screens=("home", "listing"))
    state = await build_graph(make_services(stub)).ainvoke({"run_id": "r", "user_requirement": "x"})
    assert stub.calls.count("check") == 1
    assert stub.calls.index("check") > max(i for i, c in enumerate(stub.calls) if c == "render")
    site = state["site_model"]
    assert sorted(site.screens) == ["home", "listing"]
    assert state["flow_report"].accepted and state["flow_fix"] is None
    summary = summarize(state)
    assert summary["flow"] == {
        "accepted": True,
        "steps": 0,
        "failed": [],
        "dead": [],
        "errors": [],
        "fix_source": None,
        "patches": 0,
    }
    assert summary["accepted"]


async def test_a_broken_journey_is_repaired_once_and_fails_the_run_if_still_broken():
    class Broken(StubServices):
        async def check(self, site, journey):
            self.calls.append("check")
            return FlowReport(
                steps=[FlowStep(screen="home", intent="browse", to="listing", ok=False, detail="x")]
            )

        async def flow_fix(self, plan, report, direction):
            self.calls.append("flow_fix")
            return FlowFixResult(
                status="success",
                patches=[
                    SitePlanPatch(op="add_edge", screen="home", intent="browse", to="listing")
                ],
                source="rule",
            )

    stub = Broken(screens=("home", "listing"))
    state = await build_graph(make_services(stub)).ainvoke({"run_id": "r", "user_requirement": "x"})
    assert stub.calls.count("check") == 2 and stub.calls.count("flow_fix") == 1
    # after the patch every built screen is resolved again with the repaired site map
    assert stub.calls.count("resolve") == 4
    summary = summarize(state)
    assert summary["flow"]["fix_source"] == "rule" and summary["flow"]["patches"] == 1
    assert summary["flow"]["failed"] == ["home --browse--> listing: x"]
    assert not summary["accepted"]


async def test_every_screenshot_is_taken_inside_the_site_with_a_seeded_cart():
    stub = StubServices(screens=("home",))
    await build_graph(make_services(stub)).ainvoke({"run_id": "r", "user_requirement": "x"})
    [context] = stub.render_contexts
    assert context.site.entry == "home"
    assert context.content.brand == "Stub & Co"
    assert context.state.cart == []  # the stub's content model lists nothing
