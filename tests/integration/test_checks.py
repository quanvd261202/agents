"""Directly exercises the deterministic DOM checks against handcrafted markup.

The renderer's own pages are expected to be clean, so a check that silently stopped firing would
look identical to a passing render. These cases pin both directions: what must be reported and
what must not.
"""

from __future__ import annotations

import pytest

from app.renderer.browser import CHECKS_JS

pytest.importorskip("playwright.async_api")
pytestmark = pytest.mark.integration


async def run_checks(html: str) -> list[dict]:
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            await page.set_content(
                f"<!doctype html><html><body><div data-node='root'>{html}</div></body></html>"
            )
            result = await page.evaluate(CHECKS_JS)
            return result["findings"]
        finally:
            await browser.close()


def issues(findings: list[dict], needle: str) -> list[dict]:
    return [f for f in findings if needle in f["issue"]]


LABELLED_CONTROLS = """
<label>Size <input type="radio" name="size"></label>
<label for="email">Email</label><input id="email" type="email">
<input type="text" aria-label="Search">
<input type="hidden" name="csrf">
<select aria-label="Timezone"><option>UTC</option></select>
"""


async def test_labelled_controls_are_not_reported():
    """A control named by a wrapping label, a label[for], or aria-label is correctly labelled."""
    findings = await run_checks(LABELLED_CONTROLS)
    assert not issues(findings, "no associated label"), findings


async def test_unlabelled_controls_are_reported():
    findings = await run_checks('<input type="text" name="bare"><textarea name="notes"></textarea>')
    reported = issues(findings, "no associated label")
    assert len(reported) == 2
    assert all(f["severity"] == "minor" and f["dimension"] == "accessibility" for f in reported)


async def test_label_for_pointing_at_nothing_is_still_reported():
    findings = await run_checks('<label for="missing">Name</label><input id="other" type="text">')
    assert issues(findings, "no associated label")


async def test_image_alt_text():
    findings = await run_checks('<img src="data:,x" alt="a chart"><img src="data:,y">')
    assert len(issues(findings, "missing alt text")) == 1


async def test_contrast_and_target_size_still_fire():
    findings = await run_checks(
        '<p style="color:#bbb;background:#fff;font-size:14px">faint text</p>'
        '<button style="width:12px;height:12px;padding:0">x</button>'
    )
    assert issues(findings, "contrast")
    assert issues(findings, "below 24x24")


async def test_inline_link_in_text_is_exempt_from_target_size():
    findings = await run_checks('<p>Read the <a href="#x">terms</a> first.</p>')
    assert not issues(findings, "below 24x24")
