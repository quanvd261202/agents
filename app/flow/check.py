"""The flow check: the assembled site opened in a real browser and the declared journeys walked
by clicking. Deterministic; the verdict is a fact about the site, never a model's opinion."""

from __future__ import annotations

import re
import time
from typing import Any

from app.core.exceptions import RenderError
from app.core.logging import get_logger
from app.core.telemetry import record
from app.models.flow import DeadControl, FlowReport, FlowStep
from app.models.plan import JourneyStep
from app.models.render import RenderNode
from app.models.site import SiteModel
from app.renderer.server import StaticServer

log = get_logger(__name__)

_DISPATCH_SITE = "site => window.dispatchEvent(new CustomEvent('uib:site', {detail: site}))"
_GO = (
    "href => { history.pushState(null, '', href); "
    "window.dispatchEvent(new Event('uib:navigate')); }"
)
_READY = "window.__uibReady === true"

#: How a journey intent is exercised: the control clicked, by the role the frontend stamps.
_CLICK: dict[str, str] = {
    "open_item": 'a[data-role="card"]',
    "add_to_cart": '[data-cart-add][data-role="primary_cta"], [data-cart-add][data-role="cta"]',
    "view_cart": '[data-role="cart"]',
    "go_home": '[data-role="logo"]',
    "checkout": '[data-role="primary_cta"][href], [data-role="cta"][href]',
}

_DEAD_JS = """
() => [...document.querySelectorAll(
    'a[data-role][href^="#"], button[data-role]:not([data-cart-add])')]
  .filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
  .map((el) => ({
    role: el.getAttribute('data-role'),
    node: (el.closest('[data-node]') || {}).getAttribute?.('data-node') || 'page',
    text: (el.textContent || '').trim().slice(0, 40),
  }))
"""
_ANCHORS_JS = "() => document.querySelectorAll('a[href^=\"#\"]').length"


def _semantic_by_id(node: RenderNode, out: dict[str, str] | None = None) -> dict[str, str]:
    """Node id -> semantic type, so a dead control is named by its section, not its wrapper."""
    out = {} if out is None else out
    out[node.id] = node.semantic_type
    for child in node.children:
        _semantic_by_id(child, out)
    return out


def route_pattern(route: str) -> re.Pattern[str]:
    """`/products/:id` -> a regex matching `/products/anything`."""
    parts = [r"[^/]+" if seg.startswith(":") else re.escape(seg) for seg in route.split("/")]
    return re.compile("^" + "/".join(parts) + "/?$")


class FlowChecker:
    """Satisfies app.services.interfaces.FlowCheckService."""

    def __init__(self, server: StaticServer | None = None) -> None:
        self._server = server

    async def check(self, site: SiteModel, journey: list[JourneyStep]) -> FlowReport:
        try:
            from playwright.async_api import async_playwright
        except ImportError as e:  # pragma: no cover
            raise RenderError("playwright is not installed", stage="setup") from e
        start = time.perf_counter()
        server = self._server or StaticServer()
        owns = self._server is None
        if owns:
            server.start()
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch()
                try:
                    report = await self._walk(browser, server.url, site, journey)
                finally:
                    await browser.close()
        finally:
            if owns:
                server.stop()
        ms = round((time.perf_counter() - start) * 1000, 1)
        record("flow_check", ms=ms, steps=len(report.steps), failed=len(report.failed_steps()))
        log.info(
            "flow.checked",
            steps=len(report.steps),
            failed=len(report.failed_steps()),
            dead=len(report.dead),
            ms=ms,
        )
        return report

    async def _walk(
        self, browser: Any, url: str, site: SiteModel, journey: list[JourneyStep]
    ) -> FlowReport:
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        errors: list[str] = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        first_item = self._first_item(site)
        try:
            await page.goto(url, wait_until="load")
            await page.evaluate(_DISPATCH_SITE, site.model_dump(mode="json"))
            steps = [await self._step(page, site, s, first_item) for s in journey]
            dead: list[DeadControl] = []
            anchors: dict[str, int] = {}
            for screen in site.site.screens:
                if screen.id not in site.screens:
                    continue
                await self._go(page, self._href(site, screen.id, first_item))
                semantic = _semantic_by_id(site.screens[screen.id].root)
                dead.extend(
                    DeadControl(
                        screen=screen.id,
                        role=d["role"],
                        section=semantic.get(d["node"], "page"),
                        text=d["text"],
                    )
                    for d in await page.evaluate(_DEAD_JS)
                )
                anchors[screen.id] = await page.evaluate(_ANCHORS_JS)
        finally:
            await page.close()
        return FlowReport(steps=steps, dead=dead, anchors=anchors, errors=errors[:5])

    async def _step(
        self, page: Any, site: SiteModel, step: JourneyStep, first_item: str | None
    ) -> FlowStep:
        target = site.site.screen(step.to).route
        pattern = route_pattern(target)
        if step.screen not in site.screens:
            return FlowStep(**step.model_dump(), ok=False, detail=f"'{step.screen}' was not built")
        if step.to not in site.screens:
            return FlowStep(**step.model_dump(), ok=False, detail=f"'{step.to}' was not built")
        await self._go(page, self._href(site, step.screen, first_item))
        selector = _CLICK.get(step.intent) or f'a[data-role][href^="{target.split(":")[0]}"]'
        clicked = await page.evaluate(
            """([selector, pattern]) => {
                const re = new RegExp(pattern);
                const visible = (el) => {
                  const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
                const els = [...document.querySelectorAll(selector)].filter(visible);
                const fits = (e) => !e.getAttribute('href') || re.test(e.getAttribute('href'));
                const el = els.find(fits) || els[0];
                if (!el) return null;
                el.click();
                return el.getAttribute('href') || el.tagName.toLowerCase();
            }""",
            [selector, pattern.pattern],
        )
        if clicked is None:
            return FlowStep(
                **step.model_dump(),
                ok=False,
                detail=f"no control for {step.intent} on '{step.screen}' ({selector})",
            )
        try:
            await page.wait_for_function(
                "pattern => new RegExp(pattern).test(location.pathname)",
                arg=pattern.pattern,
                timeout=4000,
            )
            await page.wait_for_function(_READY, timeout=8000)
        except Exception:  # noqa: BLE001 - a timeout is the finding, not an error
            where = await page.evaluate("location.pathname")
            return FlowStep(
                **step.model_dump(),
                ok=False,
                detail=f"clicked {clicked!r} on '{step.screen}' but landed on {where}, "
                f"not {target}",
            )
        if step.intent == "add_to_cart":
            empty = await page.evaluate("!!document.querySelector('[data-empty-cart]')")
            if empty:
                return FlowStep(**step.model_dump(), ok=False, detail="the cart stayed empty")
        return FlowStep(**step.model_dump(), ok=True, detail=f"clicked {clicked!r}")

    async def _go(self, page: Any, href: str) -> None:
        await page.evaluate(_GO, href)
        await page.wait_for_function(_READY, timeout=8000)

    @staticmethod
    def _first_item(site: SiteModel) -> str | None:
        content = site.content
        if content is None or not content.collections:
            return None
        return content.collections[0].items[0].id

    @staticmethod
    def _href(site: SiteModel, screen_id: str, item: str | None) -> str:
        return site.site.href(screen_id, item) or site.site.route(screen_id)
