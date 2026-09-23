"""Playwright renderer: RenderModel -> browser -> screenshots + deterministic findings."""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.exceptions import RenderError
from app.core.logging import get_logger
from app.core.telemetry import record
from app.models.common import Breakpoint, Dimension, Severity
from app.models.render import RenderModel, RenderResult
from app.models.site import RenderContext
from app.models.verification import Issue
from app.renderer.server import StaticServer

log = get_logger(__name__)

CHECKS_JS = (Path(__file__).parent / "checks.js").read_text()
_DISPATCH_JS = "model => window.dispatchEvent(new CustomEvent('uib:model', {detail: model}))"
_DISPATCH_SITE_JS = "site => window.dispatchEvent(new CustomEvent('uib:site', {detail: site}))"

# Scroll-triggered entrance animations start at opacity 0. A full-page screenshot taken without
# scrolling first would capture blank sections, so walk the page once and return to the top.
_SETTLE_JS = """
async () => {
  // Two frames guarantee a rendering update, which is when IntersectionObserver reports; a bare
  // timeout can elapse without one in headless Chrome, leaving an in-view entrance unfired.
  const frames = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const step = Math.round(window.innerHeight * 0.75);
  for (let y = 0; y < document.documentElement.scrollHeight; y += step) {
    window.scrollTo(0, y);
    await frames();
    await new Promise((r) => setTimeout(r, 90));
  }
  window.scrollTo(0, 0);
  await new Promise((r) => setTimeout(r, 250));
  // Motion that depends on time or scroll position jumps to its resting state, so a capture shows
  // the designed page rather than whatever frame an animation happened to be on.
  window.dispatchEvent(new Event("uib:settle"));
  await frames();
  await new Promise((r) => setTimeout(r, 50));
}
"""

# Photographs load from the network; a capture before they arrive would show their placeholders.
_IMAGES_JS = """
async () => {
  const pending = [...document.images].filter((img) => !img.complete);
  const settled = (img) => new Promise((r) => {
    img.addEventListener("load", r, { once: true });
    img.addEventListener("error", r, { once: true });
  });
  await Promise.race([Promise.all(pending.map(settled)), new Promise((r) => setTimeout(r, 8000))]);
}
"""

# Installed before the page loads: layout shift and long tasks are only observable from the start.
_PERF_JS = """
window.__uibPerf = { cls: 0, longTaskMs: 0 };
try {
  new PerformanceObserver((list) => {
    for (const e of list.getEntries()) if (!e.hadRecentInput) window.__uibPerf.cls += e.value;
  }).observe({ type: "layout-shift", buffered: true });
  new PerformanceObserver((list) => {
    for (const e of list.getEntries()) window.__uibPerf.longTaskMs += Math.max(0, e.duration - 50);
  }).observe({ type: "longtask", buffered: true });
} catch (e) {}
"""
VIEWPORTS: dict[Breakpoint, tuple[int, int]] = {
    Breakpoint.mobile: (390, 844),
    Breakpoint.tablet: (820, 1180),
    Breakpoint.desktop: (1280, 900),
    Breakpoint.wide: (1920, 1080),
}


@dataclass
class RenderOutput:
    result: RenderResult
    findings: list[Issue] = field(default_factory=list)
    outline: dict[Breakpoint, list[dict[str, Any]]] = field(default_factory=dict)


class PlaywrightRenderer:
    """Deterministic renderer. One browser per instance; reuse it across a run."""

    def __init__(
        self,
        breakpoints: list[Breakpoint] | None = None,
        *,
        screenshot_dir: Path | None = None,
        full_page: bool = True,
        server: StaticServer | None = None,
    ) -> None:
        self.breakpoints = breakpoints or [Breakpoint.mobile, Breakpoint.tablet, Breakpoint.desktop]
        self.screenshot_dir = screenshot_dir
        self.full_page = full_page
        self._server = server
        self._owns_server = server is None

    async def render(
        self, model: RenderModel, context: RenderContext | None = None
    ) -> RenderResult:
        return (await self.render_with_findings(model, context)).result

    async def render_with_findings(
        self, model: RenderModel, context: RenderContext | None = None
    ) -> RenderOutput:
        try:
            from playwright.async_api import async_playwright
        except ImportError as e:  # pragma: no cover
            raise RenderError(
                "playwright is not installed; `uv pip install -e '.[render]'`", stage="setup"
            ) from e

        start = time.perf_counter()
        server = self._server or StaticServer()
        if self._owns_server:
            server.start()
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    args=["--force-color-profile=srgb", "--font-render-hinting=none"]
                )
                try:
                    return await self._render_all(browser, server.url, model, start, context)
                finally:
                    await browser.close()
        except RenderError:
            raise
        except Exception as e:  # noqa: BLE001
            raise RenderError(
                f"render failed: {e}", stage="browser", details={"screen": model.screen_id}
            ) from e
        finally:
            if self._owns_server:
                server.stop()

    async def _render_all(
        self,
        browser: Any,
        url: str,
        model: RenderModel,
        start: float,
        context: RenderContext | None = None,
    ) -> RenderOutput:
        payload = model.model_dump(mode="json")
        site_payload = (
            {
                "site": context.site.model_dump(mode="json"),
                "content": context.content.model_dump(mode="json") if context.content else None,
                "screens": {},
            }
            if context is not None
            else None
        )
        screenshots: dict[Breakpoint, str] = {}
        findings: list[Issue] = []
        outline: dict[Breakpoint, list[dict[str, Any]]] = {}
        html = ""
        console_errors: list[str] = []

        for bp in self.breakpoints:
            width, height = VIEWPORTS[bp]
            page = await browser.new_page(
                viewport={"width": width, "height": height}, device_scale_factor=2
            )
            page.on(
                "console", lambda m: console_errors.append(m.text) if m.type == "error" else None
            )
            page.on("pageerror", lambda e: console_errors.append(str(e)))
            await page.add_init_script(_PERF_JS)
            if context is not None:
                # Seeded before the bundle loads, so the store starts from it.
                state = json.dumps(context.state.model_dump(mode="json"))
                await page.add_init_script(f"window.__uibState = {state};")
            try:
                await page.goto(url, wait_until="load")
                if site_payload is not None:
                    await page.evaluate(_DISPATCH_SITE_JS, site_payload)
                await page.evaluate(_DISPATCH_JS, payload)
                await page.wait_for_function("window.__uibReady === true", timeout=15_000)
                await page.evaluate("document.fonts ? document.fonts.ready : true")
                await page.evaluate(_IMAGES_JS)
                await page.evaluate(_SETTLE_JS)
                raw = await page.evaluate(CHECKS_JS)
                outline[bp] = raw["outline"]
                findings.extend(self._to_issues(raw["findings"], bp))
                if bp == self.breakpoints[-1]:
                    html = await page.content()
                screenshots[bp] = await self._screenshot(page, model.screen_id, bp)
            finally:
                await page.close()

        if console_errors:
            raise RenderError(
                "the page raised errors during render",
                stage="page",
                details={"errors": console_errors[:5]},
            )
        result = RenderResult(
            html=html,
            url=url,
            screenshots=screenshots,
            dom_outline=json.dumps(outline[self.breakpoints[-1]], separators=(",", ":")),
            render_time_ms=(time.perf_counter() - start) * 1000,
            findings=findings,
        )
        log.info(
            "render.complete",
            screen=model.screen_id,
            ms=round(result.render_time_ms),
            findings=len(findings),
        )
        record("render", ms=round(result.render_time_ms, 1), findings=len(findings))
        return RenderOutput(result=result, findings=findings, outline=outline)

    async def _screenshot(self, page: Any, screen_id: str, bp: Breakpoint) -> str:
        shot = await page.screenshot(full_page=self.full_page, type="png")
        if self.screenshot_dir is None:
            return base64.b64encode(shot).decode()
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = self.screenshot_dir / f"{screen_id}.{bp.value}.png"
        path.write_bytes(shot)
        return str(path)

    @staticmethod
    def _to_issues(raw: list[dict[str, Any]], bp: Breakpoint) -> list[Issue]:
        return [
            Issue(
                severity=Severity(f["severity"]),
                dimension=Dimension(f["dimension"]),
                target=f["target"],
                issue=f"[{bp.value}] {f['issue']}",
                suggestion=f["suggestion"],
                deterministic=True,
            )
            for f in raw
        ]
