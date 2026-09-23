"""M13 step 2: the site map built from the plan, and the resolver turning a screen's intent
links into hrefs on the roles components emit."""

from __future__ import annotations

from app.catalog import default_component_registry
from app.dsl import default_design_resolver
from app.graph.builder import build_graph
from app.models import (
    DesignSpec,
    ItemBinding,
    JourneyStep,
    Link,
    RenderNode,
    ScreenPlan,
    SiteMap,
    UXPlan,
)
from tests.conftest import StubServices, make_services

PLAN = UXPlan(
    product="shop",
    user_goals=["buy"],
    journey=[JourneyStep(screen="home", intent="browse", to="listing")],
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
            links=[Link(intent="open_item", to="detail"), Link(intent="go_home", to="home")],
        ),
        ScreenPlan(
            id="detail",
            purpose="evaluate",
            route="/products/:id",
            links=[Link(intent="add_to_cart", to="cart"), Link(intent="browse", to="listing")],
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
SITE = SiteMap.from_plan(PLAN)


def find(node: RenderNode, node_id: str) -> RenderNode | None:
    if node.id == node_id:
        return node
    for child in node.children:
        if (found := find(child, node_id)) is not None:
            return found
    return None


def spec(screen_id: str, recipe: str, *sections: dict) -> DesignSpec:
    return DesignSpec(
        screen_id=screen_id,
        recipe=recipe,
        visual_style="warm",
        theme="premium_light",
        sections=list(sections),
    )


# --- site map ------------------------------------------------------------------------------
def test_site_map_keeps_screen_ids_as_identity_and_routes_as_properties():
    assert SITE.entry == "home"
    assert SITE.route("detail") == "/products/:id"
    assert [(n.label, n.href) for n in SITE.nav()] == [
        ("Home", "/"),
        ("Shop", "/shop"),
        ("Cart", "/cart"),
    ]


def test_target_takes_the_first_intent_the_screen_links_with():
    assert SITE.target("cart", ["add_to_cart", "checkout"]) == "checkout"
    assert SITE.target("cart", ["sign_up"]) is None


def test_href_fills_the_item_parameter_or_declines():
    assert SITE.href("detail", "house-blend") == "/products/house-blend"
    assert SITE.href("detail") is None
    assert SITE.href("home") == "/"
    assert SITE.href("cart", "ignored") == "/cart"


def test_trail_goes_entry_then_the_screen_that_opens_this_one():
    assert SITE.trail("detail") == ["home", "listing", "detail"]
    assert SITE.trail("listing") == ["home", "listing"]
    assert SITE.trail("home") == ["home"]


# --- resolver wiring -----------------------------------------------------------------------
def test_home_roles_get_hrefs_from_the_screens_links():
    model = default_design_resolver().resolve(
        spec(
            "home",
            "ecommerce_home",
            {"id": "navigation", "type": "navigation"},
            {"id": "hero", "type": "hero"},
            {"id": "featured_products", "type": "product_grid"},
            {"id": "footer", "type": "footer"},
        ),
        site=SITE,
    )
    assert model.route == "/"
    nav = find(model.root, "navigation")
    assert nav.props["hrefs"] == {"logo": "/", "cart": "/cart", "cta": "/shop"}
    assert [n["href"] for n in nav.props["nav_links"]] == ["/", "/shop", "/cart"]
    hero = find(model.root, "hero")
    assert hero.props["hrefs"] == {"primary_cta": "/shop"}  # no learn_more link: no secondary
    assert find(model.root, "featured_products").props["hrefs"] == {"cta": "/shop"}
    assert find(model.root, "footer").props["hrefs"] == {"logo": "/"}


def test_a_bound_card_links_to_its_own_detail_route_and_an_unbound_one_does_not():
    grid = {
        "id": "featured_products",
        "type": "product_grid",
        "children": [
            {
                "id": "featured_products-item-1",
                "type": "product_card",
                "content": {"image": "beans", "title": "House Blend", "price": "$18"},
                "binding": ItemBinding(collection="products", item="house-blend"),
            },
            {
                "id": "featured_products-item-2",
                "type": "product_card",
                "content": {"image": "beans", "title": "Loose Leaf", "price": "$12"},
            },
        ],
    }
    model = default_design_resolver().resolve(
        spec(
            "home",
            "ecommerce_home",
            {"id": "navigation", "type": "navigation"},
            {"id": "hero", "type": "hero"},
            grid,
            {"id": "footer", "type": "footer"},
        ),
        site=SITE,
    )
    assert find(model.root, "featured_products-item-1").props["hrefs"] == {
        "card": "/products/house-blend"
    }
    assert "hrefs" not in find(model.root, "featured_products-item-2").props


def test_detail_wires_the_buy_box_and_breadcrumb_trail():
    model = default_design_resolver().resolve(
        spec(
            "detail",
            "ecommerce_product",
            {"id": "navigation", "type": "navigation"},
            {"id": "breadcrumb", "type": "breadcrumb"},
            {"id": "product_detail", "type": "product_detail"},
            {"id": "footer", "type": "footer"},
        ),
        site=SITE,
    )
    assert model.route == "/products/:id"
    assert find(model.root, "product_detail").props["hrefs"] == {"primary_cta": "/cart"}
    trail = find(model.root, "breadcrumb").props["trail_links"]
    assert [(t["label"], t["href"]) for t in trail] == [
        ("Home", "/"),
        ("Shop", "/shop"),
        ("detail", "/products/:id"),
    ]


def test_cart_wires_checkout_and_continue_shopping():
    model = default_design_resolver().resolve(
        spec(
            "cart",
            "ecommerce_cart",
            {"id": "navigation", "type": "navigation"},
            {"id": "cart_items", "type": "cart_items"},
            {"id": "order_summary", "type": "order_summary"},
            {"id": "footer", "type": "footer"},
        ),
        site=SITE,
    )
    assert find(model.root, "order_summary").props["hrefs"] == {"primary_cta": "/checkout"}
    assert find(model.root, "cart_items").props["hrefs"] == {"continue_cta": "/shop"}


def test_without_a_site_nothing_is_wired_and_the_gallery_still_resolves():
    model = default_design_resolver().resolve(
        spec(
            "home",
            "ecommerce_home",
            {"id": "navigation", "type": "navigation"},
            {"id": "hero", "type": "hero"},
            {"id": "featured_products", "type": "product_grid"},
            {"id": "footer", "type": "footer"},
        )
    )
    assert model.route is None
    for node_id in ("navigation", "hero", "footer"):
        props = find(model.root, node_id).props
        assert "hrefs" not in props and "nav_links" not in props


def test_every_emitted_intent_is_in_the_vocabulary():
    from app.flow import default_intent_registry

    intents = default_intent_registry()
    for comp in default_component_registry():
        for role, candidates in comp.emits.items():
            if candidates == ["*"]:
                assert role in ("nav", "trail"), comp.id
                continue
            unknown = [c for c in candidates if not intents.exists(c)]
            assert not unknown, (comp.id, role, unknown)
            if role not in ("card", "logo", "cart", "account") and comp.id != "navigation":
                assert role in comp.slot_names(), (comp.id, role)


# --- graph ----------------------------------------------------------------------------------
async def test_every_screen_is_resolved_with_the_runs_site_map():
    stub = StubServices(screens=("home", "listing"))
    state = await build_graph(make_services(stub)).ainvoke({"run_id": "r", "user_requirement": "x"})
    assert [s.entry for s in stub.sites] == ["home", "home"]
    routes = {s["screen"].id: s["resolved_design"].route for s in state["screens"]}
    assert routes == {"home": "/", "listing": "/listing"}
