"""M13 step 1: the site plan (routes, links as intents, journeys), the content model written once
per run, and the Copywriter binding list sections to its items."""

from __future__ import annotations

import pytest

from app.agents import ContentModelAgent, CopywriterAgent, DirectorAgent, PlannerAgent
from app.agents.copywriter import CopyOutput
from app.animation import default_animation_registry
from app.catalog import default_component_registry
from app.core.exceptions import ValidationError
from app.core.llm import FakeLLMProvider
from app.dsl import default_design_resolver
from app.flow import default_intent_registry, normalise_routes, validate_site_plan
from app.graph.builder import build_graph
from app.models import (
    ClarifiedRequirements,
    Collection,
    ContentItem,
    ContentModel,
    DesignDirection,
    DesignSpec,
    JourneyStep,
    Link,
    ScreenDirection,
    ScreenPlan,
    UXPlan,
)
from app.recipes import default_recipe_registry
from app.tokens import default_theme_registry
from tests.conftest import StubServices, make_services

INTENTS = default_intent_registry()
REQ = ClarifiedRequirements(
    product="Ember & Leaf",
    domain="ecommerce",
    target_audience="home baristas",
    primary_goal="sell coffee beans",
)


def shop_plan(**over) -> UXPlan:
    screens = [
        ScreenPlan(
            id="home",
            purpose="discovery",
            route="/",
            nav_label="Home",
            links=[Link(intent="browse", to="listing"), Link(intent="view_cart", to="cart")],
        ),
        ScreenPlan(
            id="listing",
            purpose="browse",
            route="/shop",
            nav_label="Shop",
            links=[Link(intent="open_item", to="detail"), Link(intent="go_home", to="home")],
        ),
        ScreenPlan(
            id="detail",
            purpose="evaluate",
            route="/products/:id",
            links=[Link(intent="add_to_cart", to="cart")],
        ),
        ScreenPlan(
            id="cart",
            purpose="review",
            route="/cart",
            links=[Link(intent="checkout", to="checkout")],
        ),
        ScreenPlan(id="checkout", purpose="pay", route="/checkout"),
    ]
    journey = [
        JourneyStep(screen="home", intent="browse", to="listing"),
        JourneyStep(screen="listing", intent="open_item", to="detail"),
        JourneyStep(screen="detail", intent="add_to_cart", to="cart"),
        JourneyStep(screen="cart", intent="checkout", to="checkout"),
    ]
    return UXPlan(product="shop", user_goals=["buy"], journey=journey, screens=screens, **over)


def with_screen(plan: UXPlan, screen_id: str, **over) -> UXPlan:
    screens = [s.model_copy(update=over) if s.id == screen_id else s for s in plan.screens]
    return plan.model_copy(update={"screens": screens})


# --- site plan validation ----------------------------------------------------------------------
def test_a_well_formed_shop_plan_validates():
    assert validate_site_plan(shop_plan(), INTENTS) is not None


def test_missing_routes_are_filled_from_screen_ids_with_the_first_as_entry():
    plan = UXPlan(
        product="p",
        user_goals=["g"],
        screens=[
            ScreenPlan(id="student_dashboard", purpose="d"),
            ScreenPlan(id="course_list", purpose="b"),
        ],
    )
    routes = [s.route for s in normalise_routes(plan).screens]
    assert routes == ["/", "/course-list"]
    validate_site_plan(normalise_routes(plan), INTENTS)


def test_an_explicit_route_on_the_first_screen_is_kept_and_the_missing_entry_reported():
    plan = UXPlan(
        product="p",
        user_goals=["g"],
        screens=[ScreenPlan(id="a", purpose="d", route="/a"), ScreenPlan(id="b", purpose="b")],
    )
    assert [s.route for s in normalise_routes(plan).screens] == ["/a", "/b"]
    with pytest.raises(ValidationError, match="route '/'"):
        validate_site_plan(normalise_routes(plan), INTENTS)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"route": "/Shop"}, "not a lowercase path"),
        ({"route": "/cart"}, "used by both"),
        ({"links": [Link(intent="teleport", to="cart")]}, "unknown intent"),
        ({"links": [Link(intent="browse", to="wishlist")]}, "not a planned screen"),
        ({"links": [Link(intent="browse", to="listing")]}, "links to itself"),
        (
            {
                "links": [
                    Link(intent="open_item", to="detail"),
                    Link(intent="open_item", to="detail"),
                ]
            },
            "repeats the link",
        ),
    ],
)
def test_bad_routes_and_links_are_named(change, message):
    plan = with_screen(shop_plan(), "listing", **change)
    plan = plan.model_copy(update={"journey": []})
    with pytest.raises(ValidationError, match=message):
        validate_site_plan(plan, INTENTS)


def test_no_entry_screen_is_an_error():
    plan = with_screen(shop_plan(), "home", route="/home").model_copy(update={"journey": []})
    with pytest.raises(ValidationError, match="route '/'"):
        validate_site_plan(plan, INTENTS)


def test_a_per_item_target_needs_an_id_segment():
    plan = with_screen(shop_plan(), "detail", route="/product")
    with pytest.raises(ValidationError, match="needs one :id segment"):
        validate_site_plan(plan, INTENTS)


def test_go_home_must_reach_the_entry_screen():
    plan = with_screen(shop_plan(), "listing", links=[Link(intent="go_home", to="cart")])
    plan = plan.model_copy(update={"journey": []})
    with pytest.raises(ValidationError, match="entry screen"):
        validate_site_plan(plan, INTENTS)


def test_a_journey_step_must_be_one_of_its_screens_links():
    plan = shop_plan().model_copy(
        update={"journey": [JourneyStep(screen="home", intent="checkout", to="checkout")]}
    )
    with pytest.raises(ValidationError, match="not one of 'home's links"):
        validate_site_plan(plan, INTENTS)


def test_journeys_are_validated_not_reachability():
    """A screen no journey visits and nothing links to is allowed: only declared paths matter."""
    plan = shop_plan().model_copy(
        update={
            "screens": [*shop_plan().screens, ScreenPlan(id="about", purpose="x", route="/about")]
        }
    )
    validate_site_plan(plan, INTENTS)


# --- planner ----------------------------------------------------------------------------------
async def test_planner_lists_the_intent_vocabulary_and_fills_routes():
    plan = shop_plan()
    plan = plan.model_copy(
        update={"screens": [s.model_copy(update={"route": None}) for s in plan.screens]}
    )
    plan = with_screen(plan, "detail", route="/products/:id")  # per-item routes can't be guessed
    llm = FakeLLMProvider([plan])
    out = await PlannerAgent(llm, default_recipe_registry()).plan(REQ)
    assert "- open_item:" in llm.calls[0][0].content
    assert [s.route for s in out.screens] == [
        "/",
        "/listing",
        "/products/:id",
        "/cart",
        "/checkout",
    ]


async def test_planner_repairs_a_journey_that_skips_a_link():
    bad = shop_plan().model_copy(
        update={"journey": [JourneyStep(screen="home", intent="checkout", to="checkout")]}
    )
    llm = FakeLLMProvider([bad, shop_plan()])
    out = await PlannerAgent(llm, default_recipe_registry()).plan(REQ)
    assert len(out.journey) == 4
    assert "not one of 'home's links" in llm.calls[1][-1].content


# --- director: intent targets against recipes --------------------------------------------------
def direction(**recipes: str) -> DesignDirection:
    return DesignDirection(
        visual_style="premium_modern",
        theme="premium_light",
        typography="modern_sans",
        radius="large",
        layout_strategy="editorial_grid",
        animation="subtle",
        screens=[ScreenDirection(screen_id=k, recipe=v) for k, v in recipes.items()],
    )


SHOP_RECIPES = dict(
    home="ecommerce_home",
    listing="ecommerce_listing",
    detail="ecommerce_product",
    cart="ecommerce_cart",
    checkout="ecommerce_checkout",
)


def make_director(llm: FakeLLMProvider) -> DirectorAgent:
    return DirectorAgent(
        llm, default_theme_registry(), default_recipe_registry(), default_animation_registry()
    )


async def test_director_accepts_recipes_that_match_the_intents():
    llm = FakeLLMProvider([direction(**SHOP_RECIPES)])
    d = await make_director(llm).direct(REQ, shop_plan())
    assert d.recipe_for("detail") == "ecommerce_product"


async def test_director_is_told_which_recipe_kind_an_intent_needs():
    wrong = direction(**{**SHOP_RECIPES, "cart": "ecommerce_home"})
    llm = FakeLLMProvider([wrong, direction(**SHOP_RECIPES)])
    d = await make_director(llm).direct(REQ, shop_plan())
    assert d.recipe_for("cart") == "ecommerce_cart"
    repair = llm.calls[1][-1].content
    assert (
        "'cart' is reached by view_cart from 'home'" in repair and "needs a cart recipe" in repair
    )


# --- content model -----------------------------------------------------------------------------
def item(i: int, **over) -> ContentItem:
    base = dict(
        id=f"roast-{i}",
        title=f"Roast No. {i}",
        subtitle="Chocolate, cherry",
        price=f"${16 + i}",
        image="bag of roasted coffee beans on oak",
        tags=["single origin", "medium"],
        attributes={"Roast": "medium"},
    )
    return ContentItem(**{**base, **over})


def content(n: int = 6, **over) -> ContentModel:
    base = dict(
        brand="Ember & Leaf",
        collections=[
            Collection(id="products", item_label="coffee", items=[item(i) for i in range(1, n + 1)])
        ],
    )
    return ContentModel(**{**base, **over})


async def test_content_agent_returns_the_model_and_asks_for_the_configured_count():
    llm = FakeLLMProvider([content()])
    plan = shop_plan()
    out = await ContentModelAgent(llm, items_per_collection=10).compose(REQ, plan, "brief text")
    assert out.brand == "Ember & Leaf"
    assert "`items`: 10 for the main collection" in llm.calls[0][0].content
    assert "brief text" in llm.calls[0][1].content


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (content(brand="[brand]"), "real wordmark"),
        (content(n=3), "write at least 4"),
        (
            content().model_copy(
                update={
                    "collections": [
                        Collection(
                            id="products",
                            item_label="coffee",
                            items=[item(1), item(2), item(3), item(4, id="roast-1")],
                        )
                    ]
                }
            ),
            "duplicate item ids",
        ),
        (
            content().model_copy(
                update={
                    "collections": [
                        Collection(
                            id="products",
                            item_label="coffee",
                            items=[item(1), item(2), item(3), item(4, title="Roast No. 1")],
                        )
                    ]
                }
            ),
            "duplicate item titles",
        ),
        (
            content().model_copy(
                update={
                    "collections": [
                        Collection(
                            id="products",
                            item_label="coffee",
                            items=[item(1), item(2), item(3), item(4, id="Roast 4")],
                        )
                    ]
                }
            ),
            "must be a slug",
        ),
        (
            content().model_copy(
                update={
                    "collections": [
                        Collection(
                            id="Products", item_label="coffee", items=[item(i) for i in range(4)]
                        )
                    ]
                }
            ),
            "snake_case",
        ),
    ],
)
async def test_content_agent_rejects_bad_catalogues(bad, message):
    llm = FakeLLMProvider([bad, bad, bad])
    with pytest.raises(ValidationError, match=message):
        await ContentModelAgent(llm).compose(REQ, shop_plan())


async def test_a_product_that_lists_nothing_has_no_collections():
    llm = FakeLLMProvider([ContentModel(brand="Ledger")])
    out = await ContentModelAgent(llm).compose(REQ, shop_plan())
    assert out.collections == []


# --- copywriter binding ------------------------------------------------------------------------
SCREEN = shop_plan().screen("home")
DIRECTION = direction(**SHOP_RECIPES)
HOME = DesignSpec(
    screen_id="home",
    recipe="ecommerce_home",
    visual_style="warm_editorial",
    theme="premium_light",
    sections=[
        {"id": "navigation", "type": "navigation"},
        {"id": "hero", "type": "hero"},
        {"id": "featured_products", "type": "product_grid", "variant": "premium"},
        {"id": "footer", "type": "footer"},
    ],
)
DETAIL = DesignSpec(
    screen_id="detail",
    recipe="ecommerce_product",
    visual_style="warm_editorial",
    theme="premium_light",
    sections=[
        {"id": "navigation", "type": "navigation"},
        {"id": "product_detail", "type": "product_detail"},
        {"id": "footer", "type": "footer"},
    ],
)


def find_node(node, node_id: str):
    if node.id == node_id:
        return node
    for child in node.children:
        if (found := find_node(child, node_id)) is not None:
            return found
    return None


def words(section_id: str, **slots: str) -> dict:
    return {"id": section_id, "slots": [{"slot": k, "text": v} for k, v in slots.items()]}


def home_copy(**grid_extra) -> CopyOutput:
    return CopyOutput.model_validate(
        {
            "sections": [
                words("navigation", logo="Ember & Leaf"),
                words("hero", headline="Roasted this week", media="steaming pour-over on a bench"),
                {**words("featured_products", title="Bestsellers"), **grid_extra},
                words("footer", tagline="Small batches, sent fresh"),
            ]
        }
    )


def writer(*responses) -> CopywriterAgent:
    return CopywriterAgent(FakeLLMProvider(list(responses)), default_component_registry())


async def test_list_sections_bind_to_collection_items_and_carry_their_ids():
    ids = [f"roast-{i}" for i in range(1, 7)]
    spec = await writer(home_copy(item_ids=ids)).write(
        REQ, SCREEN, DIRECTION, HOME, content=content()
    )
    grid = spec.find("featured_products")
    assert [c.binding.item for c in grid.children] == ids
    assert grid.children[0].binding.collection == "products"
    assert grid.children[0].content == {
        "title": "Roast No. 1",
        "note": "Chocolate, cherry",
        "price": "$17",
        "image": "bag of roasted coffee beans on oak",
    }
    assert grid.children[0].variant == "premium"
    model = default_design_resolver().resolve(spec)
    card = find_node(model.root, "featured_products-item-1")
    assert card.props["binding"] == {"collection": "products", "item": "roast-1"}


async def test_the_prompt_lists_the_collections_and_asks_for_ids():
    llm = FakeLLMProvider([home_copy(item_ids=[f"roast-{i}" for i in range(1, 7)])])
    await CopywriterAgent(llm, default_component_registry()).write(
        REQ, SCREEN, DIRECTION, HOME, content=content()
    )
    user = llm.calls[0][1].content
    assert "Brand: Ember & Leaf" in user
    assert "roast-1 - Roast No. 1 - $17" in user
    assert "featured_products (product_grid, variant premium)" in user
    assert "item_ids: pick 6" in user and "items: 6 product cards" not in user


async def test_written_items_are_refused_when_a_collection_exists():
    free = [
        {"title": f"Blend {i}", "note": "", "price": "$18", "image": "coffee beans"}
        for i in range(1, 7)
    ]
    ok = home_copy(item_ids=[f"roast-{i}" for i in range(1, 7)])
    llm = FakeLLMProvider([home_copy(items=free), ok])
    await CopywriterAgent(llm, default_component_registry()).write(
        REQ, SCREEN, DIRECTION, HOME, content=content()
    )
    assert "pick item_ids from the collections, not write items" in llm.calls[1][-1].content


@pytest.mark.parametrize(
    ("ids", "message"),
    [
        (["roast-1", "roast-99"], "in no collection"),
        (["roast-1", "roast-1"], "repeats an item id"),
        ([], "pick their item_ids"),
    ],
)
async def test_bad_item_ids_are_handed_back(ids, message):
    bad = home_copy(item_ids=ids)
    with pytest.raises(ValidationError, match=message):
        await writer(bad, bad, bad).write(REQ, SCREEN, DIRECTION, HOME, content=content())


async def test_items_from_two_collections_cannot_share_a_section():
    two = content().model_copy(
        update={
            "collections": [
                *content().collections,
                Collection(
                    id="gear", item_label="tool", items=[item(i, id=f"gear-{i}") for i in range(4)]
                ),
            ]
        }
    )
    bad = home_copy(item_ids=["roast-1", "gear-1"])
    with pytest.raises(ValidationError, match="mixes items"):
        await writer(bad, bad, bad).write(REQ, SCREEN, DIRECTION, HOME, content=two)


async def test_without_a_collection_the_writer_still_writes_items_itself():
    free = [
        {"title": f"Blend {i}", "note": "", "price": "$18", "image": "coffee beans"}
        for i in range(1, 7)
    ]
    spec = await writer(home_copy(items=free)).write(
        REQ, SCREEN, DIRECTION, HOME, content=ContentModel(brand="Ember & Leaf")
    )
    grid = spec.find("featured_products")
    assert len(grid.children) == 6 and grid.children[0].binding is None
    bad = home_copy(item_ids=["roast-1"])
    with pytest.raises(ValidationError, match="no collections"):
        await writer(bad, bad, bad).write(
            REQ, SCREEN, DIRECTION, HOME, content=ContentModel(brand="X")
        )


async def test_a_detail_section_binds_one_item_and_its_facts_win():
    copy = CopyOutput.model_validate(
        {
            "sections": [
                words("navigation", logo="Ember & Leaf"),
                {
                    **words("product_detail", title="Wrong Name", description="Balanced and sweet"),
                    "item_ids": ["roast-2"],
                },
                words("footer", tagline="Small batches"),
            ]
        }
    )
    spec = await writer(copy).write(
        REQ, shop_plan().screen("detail"), DIRECTION, DETAIL, content=content()
    )
    detail = spec.find("product_detail")
    assert detail.binding.item == "roast-2"
    assert detail.content["title"] == "Roast No. 2"
    assert detail.content["price"] == "$18"
    assert detail.content["description"] == "Balanced and sweet"
    assert "media" not in detail.content  # the gallery stays the writer's

    two = copy.model_copy(deep=True)
    two.sections[1].item_ids = ["roast-1", "roast-2"]
    with pytest.raises(ValidationError, match="exactly one id"):
        await writer(two, two, two).write(REQ, SCREEN, DIRECTION, DETAIL, content=content())


# --- graph -------------------------------------------------------------------------------------
async def test_the_content_model_is_composed_once_and_reaches_every_copywriter():
    stub = StubServices(screens=("home", "listing", "detail"))
    state = await build_graph(make_services(stub)).ainvoke({"run_id": "r", "user_requirement": "x"})
    assert stub.calls.count("compose") == 1
    assert state["content_model"].brand == "Stub & Co"
    assert [c.brand for c in stub.contents] == ["Stub & Co"] * 3
    assert stub.calls.index("compose") > stub.calls.index("direct")
    assert stub.calls.index("compose") < stub.calls.index("build")
