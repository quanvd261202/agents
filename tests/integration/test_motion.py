"""M8: the motion runtime in a real browser. Skipped when the bundle or playwright is absent."""

from __future__ import annotations

import pytest

from app.dsl import default_design_resolver
from app.models.common import Intensity
from app.models.dsl import SectionSpec
from app.models.render import MotionBehavior, RenderModel
from app.renderer import StaticServer
from app.renderer.browser import _DISPATCH_JS, _PERF_JS, _SETTLE_JS, CHECKS_JS
from app.renderer.server import FRONTEND_DIST

pytest.importorskip("playwright.async_api")
pytestmark = [
    pytest.mark.skipif(
        not (FRONTEND_DIST / "index.html").exists(), reason="frontend bundle not built"
    ),
    pytest.mark.integration,
]

HIDDEN = "[...document.querySelectorAll('[data-node] *')].filter(e => e.style.opacity === '0')"
TICKED = (
    "() => [...document.querySelectorAll('[data-node=stats_band] *')]"
    ".filter(e => e.style.fontVariantNumeric)"
)
REST_STATE = f"""() => ({{
  hidden: {HIDDEN}.length,
  heading: document.querySelector('[data-node=hero] h1').textContent,
  words: document.querySelectorAll('[data-node=hero] .uib-word').length,
  moved: [...document.querySelectorAll('.uib-word-inner')]
    .filter(w => w.style.transform).length,
  revealed: document.querySelector('[data-node=hero] h1').classList.contains('uib-revealed'),
}})"""
LAYER = "[data-node=image_band] [data-motion-layer]"
LAYER_TRANSFORM = f"() => getComputedStyle(document.querySelector('{LAYER}')).transform"

PAGE = [
    ("navigation", None),
    ("hero", "editorial"),
    ("product_grid", None),
    ("stats_band", None),
    ("image_band", None),
    ("footer", None),
]


def page(intensity: Intensity = Intensity.moderate, **kw) -> RenderModel:
    # A nav whose actions include the cart: the add-to-cart flight needs somewhere to land.
    content = {"navigation": {"actions": "Search,Cart"}}
    sections = [SectionSpec(id=t, type=t, variant=v, content=content.get(t, {})) for t, v in PAGE]
    return default_design_resolver().preview(
        sections, palette="espresso", intensity=intensity, **kw
    )


@pytest.fixture(scope="module")
def server():
    with StaticServer() as s:
        yield s


@pytest.fixture
async def browser():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        yield b
        await b.close()


async def open_page(browser, server, model: RenderModel, *, settle: bool, width: int = 1280):
    p = await browser.new_page(viewport={"width": width, "height": 900})
    await p.add_init_script(_PERF_JS)
    await p.goto(server.url)
    await p.evaluate(_DISPATCH_JS, model.model_dump(mode="json"))
    await p.wait_for_function("window.__uibReady === true")
    if settle:
        await p.evaluate(_SETTLE_JS)
    return p


async def test_a_settled_page_is_at_rest_with_its_text_intact(browser, server):
    model = page()
    p = await open_page(browser, server, model, settle=True)
    state = await p.evaluate(REST_STATE)
    assert state["hidden"] == 0  # every staggered item ended visible
    assert state["words"] > 2 and state["moved"] == 0 and state["revealed"]
    hero = next(n for n in model.root.children if n.id == "hero")
    assert "headline_reveal" in {b.name for b in hero.motion}
    # the heading's text is the component's own text, split into masks but never rewritten
    assert state["heading"] == "Crafted slowly. Made to be savoured."
    findings = (await p.evaluate(CHECKS_JS))["findings"]
    assert not [f for f in findings if f["severity"] == "critical"]


async def test_count_up_runs_live_and_lands_on_the_real_value(browser, server):
    p = await open_page(browser, server, page(), settle=False)
    stats = p.locator("[data-node=stats_band]")
    await stats.scroll_into_view_if_needed()
    finals = await p.evaluate(TICKED + ".length")
    assert finals > 0  # the ticker found numbers to count
    await p.wait_for_timeout(2500)
    settled = await p.evaluate(TICKED + ".map(e => e.textContent)")
    live = await open_page(browser, server, page(), settle=True)
    at_rest = await live.evaluate(TICKED + ".map(e => e.textContent)")
    assert settled == at_rest  # counting ends exactly on the designed value


async def test_scroll_zoom_moves_with_the_page(browser, server):
    p = await open_page(browser, server, page(), settle=False)
    before = await p.evaluate(LAYER_TRANSFORM)
    await p.locator("[data-node=image_band]").scroll_into_view_if_needed()
    await p.evaluate("() => window.scrollBy(0, 200)")
    await p.wait_for_timeout(300)
    after = await p.evaluate(LAYER_TRANSFORM)
    assert before != after


async def test_reduced_motion_runs_no_behaviour(browser, server):
    model = page()
    model.reduced_motion = True
    p = await open_page(browser, server, model, settle=False)
    marks = "document.querySelectorAll('.uib-word, .uib-lift, .uib-drift').length"
    touched = await p.evaluate(f"() => {marks} + {HIDDEN}.length")
    assert touched == 0


async def test_adding_a_product_flies_it_to_the_cart_and_bumps_the_count(browser, server):
    p = await open_page(browser, server, page(), settle=True)
    count = p.locator("[data-cart-count]")
    before = int(await count.text_content())
    await p.get_by_role("button", name="Quick add").first.click()
    await p.wait_for_timeout(900)
    assert int(await count.text_content()) == before + 1


async def test_the_budget_check_fires_when_too_many_loops_run(browser, server):
    model = page(intensity=Intensity.subtle)
    for node in model.root.children:
        node.motion = [MotionBehavior(name="gradient_drift", params={"amplitude": 0.2})]
    p = await open_page(browser, server, model, settle=False)
    findings = (await p.evaluate(CHECKS_JS))["findings"]
    assert any("continuous animations" in f["issue"] for f in findings)


async def test_a_choreographed_page_does_not_shift_its_layout(browser, server):
    p = await open_page(browser, server, page(intensity=Intensity.expressive), settle=True)
    cls = await p.evaluate("() => window.__uibPerf.cls")
    assert cls <= 0.1
