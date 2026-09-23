"""M10 content in the pipeline: written copy survives the fix loop and the graph runs the
copywriter and imagery once per screen, between build and resolve."""

from __future__ import annotations

from app.agents import FixerAgent
from app.catalog import default_component_registry
from app.core.llm import FakeLLMProvider
from app.dsl import default_design_resolver
from app.graph.builder import build_graph
from app.models import DesignSpec, FixResult, ImageRef, Patch
from app.recipes import default_recipe_registry
from tests.conftest import StubServices, make_services

SPEC = DesignSpec(
    screen_id="home",
    recipe="ecommerce_home",
    visual_style="m",
    theme="modern_light",
    sections=[
        {"id": "navigation", "type": "navigation"},
        {"id": "hero", "type": "hero", "content": {"headline": "Coffee worth waking for"}},
        {
            "id": "featured_products",
            "type": "product_grid",
            "content": {"title": "This week's roasts"},
            "children": [
                {
                    "id": "featured_products-item-1",
                    "type": "product_card",
                    "content": {"image": "beans", "title": "Ember", "price": "$18"},
                }
            ],
        },
        {
            "id": "newsletter",
            "type": "newsletter_signup",
            "content": {
                "title": "Stay in the loop",
                "submit": "Join",
                "privacy": "No spam, ever.",
                "media": "steam rising from a ceramic cup",
            },
            "images": {"media": [ImageRef(url="https://p/steam.jpg")]},
        },
        {"id": "footer", "type": "footer"},
    ],
)


def fixer() -> FixerAgent:
    return FixerAgent(
        FakeLLMProvider(),
        default_recipe_registry(),
        default_component_registry(),
        default_design_resolver(),
    )


def patched(target: str, prop: str, value: str) -> DesignSpec:
    fix = FixResult(status="success", patches=[Patch(target=target, property=prop, value=value)])
    return fixer().apply(SPEC, fix)


# --- the fixer -------------------------------------------------------------------------------
def test_a_type_patch_keeps_only_the_copy_the_new_component_can_show():
    spec = patched("newsletter", "type", "subscription_offer")
    section = spec.find("newsletter")
    assert section is not None and section.type == "subscription_offer"
    assert section.content == {
        "title": "Stay in the loop",
        "media": "steam rising from a ceramic cup",
    }
    assert section.images == {"media": [ImageRef(url="https://p/steam.jpg")]}  # slot still exists
    default_design_resolver().resolve(spec)  # the patched spec resolves with its copy in place


def test_a_type_patch_drops_product_cards_the_new_component_cannot_hold():
    spec = patched("featured_products", "type", "collection_grid")
    section = spec.find("featured_products")
    assert section is not None
    assert section.children == []
    assert section.content == {"title": "This week's roasts"}


def test_other_patches_leave_copy_and_photos_alone():
    spec = patched("newsletter", "variant", "card")
    assert spec.find("newsletter") == SPEC.find("newsletter").model_copy(  # type: ignore[union-attr]
        update={"variant": "card"}
    )


# --- the graph -------------------------------------------------------------------------------
START = {"run_id": "r", "user_requirement": "A coffee roaster's shop: Ember Roast, Sunday Blend"}


async def test_copy_and_photos_come_after_build_and_before_resolve(stub):
    await build_graph(make_services(stub)).ainvoke(START)
    i = stub.calls.index("build")
    assert stub.calls[i : i + 4] == ["build", "write", "illustrate", "resolve"]


async def test_the_brief_reaches_the_copywriter_verbatim(stub):
    await build_graph(make_services(stub)).ainvoke(START)
    assert stub.copy_briefs == [START["user_requirement"]]


async def test_the_fix_loop_does_not_rewrite_the_copy():
    stub = StubServices(fail_times=2)
    await build_graph(make_services(stub)).ainvoke(START)
    assert stub.calls.count("render") == 3
    assert stub.calls.count("write") == stub.calls.count("illustrate") == 1
