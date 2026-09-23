"""M13 in a real browser: a shop assembled from the golden specs, with bound cards and a content
model, is walked along its journey by clicking. Home -> listing -> a product -> the cart (with the
product in it) -> checkout. Skipped when the bundle or playwright is absent."""

from __future__ import annotations

import pytest

from app.dsl import default_design_resolver
from app.flow import assemble_site
from app.flow.check import FlowChecker, route_pattern
from app.models import (
    Collection,
    ContentItem,
    ContentModel,
    DesignSpec,
    ItemBinding,
    JourneyStep,
    Link,
    ScreenPlan,
    SiteMap,
    UXPlan,
)
from app.renderer import StaticServer
from app.renderer.server import FRONTEND_DIST
from tests.fixtures.specs import ALL

pytest.importorskip("playwright.async_api")
pytestmark = [
    pytest.mark.skipif(
        not (FRONTEND_DIST / "index.html").exists(), reason="frontend bundle not built"
    ),
    pytest.mark.integration,
]

ITEMS = [
    ContentItem(
        id=f"roast-{i}",
        title=f"Roast No. {i}",
        subtitle="Chocolate, cherry, a long finish",
        price=f"${15 + i}.00",
        image="bag of roasted coffee beans on oak",
        tags=["single origin" if i % 2 else "blend", "medium" if i < 4 else "dark"],
        attributes=[{"label": "Roast", "value": "medium"}, {"label": "Weight", "value": "250 g"}],
    )
    for i in range(1, 7)
]
CONTENT = ContentModel(
    brand="Ember & Leaf",
    collections=[Collection(id="products", item_label="coffee", items=ITEMS)],
)
PLAN = UXPlan(
    product="shop",
    user_goals=["buy"],
    journey=[
        JourneyStep(screen="home", intent="browse", to="listing"),
        JourneyStep(screen="listing", intent="open_item", to="detail"),
        JourneyStep(screen="detail", intent="add_to_cart", to="cart"),
        JourneyStep(screen="cart", intent="checkout", to="checkout"),
    ],
    screens=[
        ScreenPlan(
            id="home",
            purpose="discovery",
            route="/",
            nav_label="Home",
            links=[
                Link(intent="browse", to="listing"),
                Link(intent="view_cart", to="cart"),
                Link(intent="open_item", to="detail"),
            ],
        ),
        ScreenPlan(
            id="listing",
            purpose="browse",
            route="/shop",
            nav_label="Shop",
            links=[
                Link(intent="open_item", to="detail"),
                Link(intent="view_cart", to="cart"),
                Link(intent="go_home", to="home"),
            ],
        ),
        ScreenPlan(
            id="detail",
            purpose="evaluate",
            route="/products/:id",
            links=[
                Link(intent="add_to_cart", to="cart"),
                Link(intent="browse", to="listing"),
                Link(intent="view_cart", to="cart"),
            ],
        ),
        ScreenPlan(
            id="cart",
            purpose="review",
            route="/cart",
            nav_label="Cart",
            links=[Link(intent="checkout", to="checkout"), Link(intent="browse", to="listing")],
        ),
        ScreenPlan(id="checkout", purpose="pay", route="/checkout"),
    ],
)


def card(parent: str, item: ContentItem, variant: str | None = None) -> dict:
    return {
        "id": f"{parent}-item-{item.id}",
        "type": "product_card",
        "variant": variant,
        "content": {
            "image": item.image,
            "title": item.title,
            "price": item.price,
            "note": item.subtitle,
        },
        "binding": ItemBinding(collection="products", item=item.id),
    }


def with_cards(spec: dict, section_id: str, items: list[ContentItem], variant=None) -> dict:
    sections = [
        {**s, "children": [card(section_id, i, variant) for i in items]}
        if s["id"] == section_id
        else s
        for s in spec["sections"]
    ]
    return {**spec, "sections": sections}


def specs() -> dict[str, DesignSpec]:
    home = with_cards(ALL["ecommerce_home"], "featured_products", ITEMS[:6], "premium")
    listing = with_cards(ALL["ecommerce_listing"], "product_grid", ITEMS)
    detail = {**ALL["ecommerce_product"], "screen_id": "detail"}
    detail = {
        **detail,
        "sections": [
            {
                **s,
                "content": {"title": ITEMS[0].title, "price": ITEMS[0].price},
                "binding": ItemBinding(collection="products", item=ITEMS[0].id),
            }
            if s["id"] == "product_detail"
            else s
            for s in detail["sections"]
        ],
    }
    detail = with_cards(detail, "related_products", ITEMS[1:5], "premium")
    cart = with_cards(ALL["ecommerce_cart"], "cross_sell", ITEMS[2:6], "premium")
    checkout = ALL["ecommerce_checkout"]
    return {
        sid: DesignSpec.model_validate({**raw, "screen_id": sid})
        for sid, raw in [
            ("home", home),
            ("listing", listing),
            ("detail", detail),
            ("cart", cart),
            ("checkout", checkout),
        ]
    }


@pytest.fixture(scope="module")
def server():
    with StaticServer() as s:
        yield s


@pytest.fixture(scope="module")
def site():
    site_map = SiteMap.from_plan(PLAN)
    resolver = default_design_resolver()
    models = {sid: resolver.resolve(spec, site=site_map) for sid, spec in specs().items()}
    return assemble_site(PLAN, CONTENT, models)


def test_route_patterns():
    assert route_pattern("/products/:id").match("/products/roast-3")
    assert not route_pattern("/products/:id").match("/products")
    assert route_pattern("/").match("/")


async def test_the_journey_arrives_by_clicking(server, site):
    report = await FlowChecker(server=server).check(site, PLAN.journey)
    assert report.errors == [], report.errors
    assert [s.ok for s in report.steps] == [True] * 4, [s.detail for s in report.steps]
    # the product opened is the one whose card was clicked
    assert "/products/roast-" in report.steps[1].detail
    # what leads nowhere is named by screen, section and role: the hero's second button wants
    # learn_more and the plan has no such page; the listing's "view all" would browse itself
    dead = [(d.screen, d.section, d.role) for d in report.dead]
    assert dead == [("home", "hero", "secondary_cta"), ("listing", "product_grid", "cta")], dead


async def test_a_dead_control_is_reported_when_the_screen_never_links_its_intent(server):
    plan = PLAN.model_copy(
        update={
            "screens": [
                s.model_copy(update={"links": [Link(intent="browse", to="listing")]})
                if s.id == "detail"
                else s
                for s in PLAN.screens
            ],
            "journey": [],
        }
    )
    site_map = SiteMap.from_plan(plan)
    resolver = default_design_resolver()
    detail = specs()["detail"]
    models = {"detail": resolver.resolve(detail, site=site_map)}
    report = await FlowChecker(server=server).check(assemble_site(plan, CONTENT, models), [])
    assert report.errors == []
    # the buy box's add-to-cart button still works locally (a button, not dead); the nav's cart
    # icon, however, has no cart to reach
    roles = {(d.section, d.role) for d in report.dead}
    assert ("navigation", "cart") in roles or ("product_detail", "primary_cta") not in roles
