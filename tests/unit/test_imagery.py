"""M10 imagery: photographs for image slots from a scripted provider; no network."""

from __future__ import annotations

import httpx
import pytest

from app.core.exceptions import ConfigurationError, ValidationError
from app.dsl import default_design_resolver
from app.imagery import FakeImageProvider, Illustrator, PexelsImageProvider, build_image_provider
from app.models import DesignSpec, ImageRef, RenderNode

BEANS = "coffee beans in a scoop"
SPEC = DesignSpec(
    screen_id="home",
    recipe="ecommerce_home",
    visual_style="m",
    theme="modern_light",
    sections=[
        {"id": "navigation", "type": "navigation"},
        {
            "id": "hero",
            "type": "hero",
            "content": {"headline": "Coffee worth waking for", "media": "pour-over coffee on oak"},
        },
        {
            "id": "collections",
            "type": "collection_grid",
            "content": {
                "collections": "Beans,Tea,Gear",
                "media": f"{BEANS}, loose leaf tea, ceramic pour-over",
            },
        },
        {
            "id": "featured_products",
            "type": "product_grid",
            "children": [
                {
                    "id": f"featured_products-item-{i}",
                    "type": "product_card",
                    "content": {"image": BEANS, "title": t, "price": "$18"},
                }
                for i, t in ((1, "Ember"), (2, "Ash"))
            ],
        },
        {"id": "footer", "type": "footer"},
    ],
)


def section(spec: DesignSpec, sid: str):
    s = spec.find(sid)
    assert s is not None
    return s


# --- the service -----------------------------------------------------------------------------
async def test_every_image_slot_gets_a_photograph_in_order():
    spec = await Illustrator(FakeImageProvider()).illustrate(SPEC)
    hero = section(spec, "hero")
    assert [r.url for r in hero.images["media"]] == [
        "https://images.test/pour-over-coffee-on-oak-1.jpg"
    ]
    assert hero.content == section(SPEC, "hero").content  # the words are untouched
    tiles = section(spec, "collections").images["media"]
    assert [r.alt for r in tiles] == [BEANS, "loose leaf tea", "ceramic pour-over"]
    for card in section(spec, "featured_products").children:
        assert card.images["image"][0].url.startswith("https://images.test/coffee-beans")
    assert section(spec, "navigation").images == {} and section(spec, "footer").images == {}


async def test_the_same_description_never_repeats_a_photo_on_one_page():
    spec = await Illustrator(FakeImageProvider()).illustrate(SPEC)
    urls = [
        section(spec, "collections").images["media"][0].url,
        *(c.images["image"][0].url for c in section(spec, "featured_products").children),
    ]
    assert len(set(urls)) == 3


async def test_a_description_is_searched_once_per_service():
    provider = FakeImageProvider()
    service = Illustrator(provider)
    await service.illustrate(SPEC)
    assert provider.queries.count(BEANS) == 1  # three uses, one search
    searched = len(provider.queries)
    await service.illustrate(SPEC.model_copy(update={"screen_id": "listing"}))
    assert len(provider.queries) == searched  # another screen reuses the cache


async def test_a_provider_failure_leaves_the_placeholders_and_the_screen_alive():
    assert await Illustrator(FakeImageProvider(fail=True)).illustrate(SPEC) == SPEC


async def test_nothing_found_keeps_list_positions_aligned():
    provider = FakeImageProvider(
        results={
            BEANS: [ImageRef(url="https://p/a.jpg")],
            "ceramic pour-over": [ImageRef(url="https://p/c.jpg")],
        }
    )
    spec = await Illustrator(provider).illustrate(SPEC)
    tiles = section(spec, "collections").images["media"]
    assert [r.url for r in tiles] == ["https://p/a.jpg", "", "https://p/c.jpg"]
    assert "media" not in section(spec, "hero").images  # nothing at all: slot left out


async def test_a_slot_already_sourced_is_not_searched_again():
    sourced = SPEC.model_copy(
        update={
            "sections": [
                s.model_copy(update={"images": {"media": [ImageRef(url="https://p/kept.jpg")]}})
                if s.id == "hero"
                else s
                for s in SPEC.sections
            ]
        }
    )
    provider = FakeImageProvider()
    spec = await Illustrator(provider).illustrate(sourced)
    assert "pour-over coffee on oak" not in provider.queries
    assert section(spec, "hero").images["media"][0].url == "https://p/kept.jpg"


async def test_no_provider_means_no_change():
    assert await Illustrator(None).illustrate(SPEC) is SPEC


# --- the resolver hands photographs to the frontend ------------------------------------------
def _walk(n: RenderNode):
    yield n
    for c in n.children:
        yield from _walk(c)


async def test_resolver_passes_images_through_as_props():
    spec = await Illustrator(FakeImageProvider()).illustrate(SPEC)
    model = default_design_resolver().resolve(spec)
    by_id = {n.id: n for n in _walk(model.root)}
    assert by_id["hero"].props["images"]["media"][0] == {
        "url": "https://images.test/pour-over-coffee-on-oak-1.jpg",
        "alt": "pour-over coffee on oak",
        "credit": "Fake",
    }
    assert len(by_id["collections"].props["images"]["media"]) == 3
    assert "images" in by_id["featured_products-item-1"].props
    assert "images" not in by_id["footer"].props


def test_resolver_rejects_images_for_a_slot_the_component_lacks():
    bad = SPEC.model_copy(
        update={
            "sections": [
                s.model_copy(update={"images": {"portrait": [ImageRef(url="https://p/x.jpg")]}})
                if s.id == "hero"
                else s
                for s in SPEC.sections
            ]
        }
    )
    with pytest.raises(ValidationError, match="invalid image slots for hero"):
        default_design_resolver().resolve(bad)


def test_images_round_trip_through_the_saved_spec():
    spec = SPEC.model_copy(
        update={
            "sections": [
                s.model_copy(
                    update={"images": {"media": [ImageRef(url="https://p/1.jpg", credit="A")]}}
                )
                if s.id == "hero"
                else s
                for s in SPEC.sections
            ]
        }
    )
    again = DesignSpec.model_validate_json(spec.model_dump_json(exclude_defaults=True))
    assert again == spec


# --- providers -------------------------------------------------------------------------------
async def test_pexels_maps_photos_and_sends_the_key():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "photos": [
                    {
                        "src": {"large2x": "https://images.pexels.com/1.jpeg", "large": "x"},
                        "alt": "Coffee beans",
                        "photographer": "Ana",
                    },
                    {"src": {"large2x": "https://images.pexels.com/2.jpeg"}},
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    refs = await PexelsImageProvider("k3y", client).search("coffee beans", 3)
    assert refs == [
        ImageRef(url="https://images.pexels.com/1.jpeg", alt="Coffee beans", credit="Ana"),
        ImageRef(url="https://images.pexels.com/2.jpeg"),
    ]
    [request] = seen
    assert request.headers["Authorization"] == "k3y"
    assert request.url.params["query"] == "coffee beans"
    assert request.url.params["per_page"] == "3"


async def test_pexels_http_errors_surface_to_the_service_which_swallows_them():
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(429)))
    provider = PexelsImageProvider("k", client)
    with pytest.raises(httpx.HTTPStatusError):
        await provider.search("x", 1)
    assert await Illustrator(provider).illustrate(SPEC) == SPEC


def test_build_image_provider():
    assert build_image_provider("none") is None
    assert isinstance(build_image_provider("fake"), FakeImageProvider)
    assert isinstance(build_image_provider("pexels", "key"), PexelsImageProvider)
    with pytest.raises(ConfigurationError, match="PEXELS_API_KEY"):
        build_image_provider("pexels", None)
    with pytest.raises(ConfigurationError, match="Unknown image provider"):
        build_image_provider("shutterstock", "key")
