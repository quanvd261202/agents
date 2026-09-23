"""Renders every golden spec in a real browser. Skipped when the bundle or playwright is absent."""

from __future__ import annotations

import json

import pytest

from app.dsl import default_design_resolver
from app.models import DesignSpec
from app.models.common import Breakpoint
from app.renderer import PlaywrightRenderer, StaticServer
from app.renderer.server import FRONTEND_DIST
from tests.fixtures.specs import ALL

pytest.importorskip("playwright.async_api")
pytestmark = [
    pytest.mark.skipif(
        not (FRONTEND_DIST / "index.html").exists(), reason="frontend bundle not built"
    ),
    pytest.mark.integration,
]


@pytest.fixture(scope="module")
def server():
    with StaticServer() as s:
        yield s


@pytest.fixture(scope="module")
def resolver():
    return default_design_resolver()


async def _render(server, resolver, name, tmp_path, **kw):
    model = resolver.resolve(DesignSpec.model_validate(ALL[name]), **kw)
    renderer = PlaywrightRenderer(server=server, screenshot_dir=tmp_path)
    return model, await renderer.render_with_findings(model)


@pytest.mark.parametrize("name", list(ALL))
async def test_every_recipe_renders_cleanly(server, resolver, name, tmp_path):
    model, out = await _render(server, resolver, name, tmp_path)

    # screenshots exist at all three breakpoints and are non-trivial
    assert set(out.result.screenshots) == {Breakpoint.mobile, Breakpoint.tablet, Breakpoint.desktop}
    for path in out.result.screenshots.values():
        assert (tmp_path / path.rsplit("/", 1)[-1]).stat().st_size > 5_000

    # every section in the spec appears in the rendered DOM
    rendered = {n["id"] for n in json.loads(out.result.dom_outline)}
    for section in model.root.children:
        assert section.id in rendered or section.id == "main"

    critical = [f for f in out.findings if f.severity == "critical"]
    assert not critical, [f.issue for f in critical]


@pytest.mark.parametrize("name", list(ALL))
async def test_no_accessibility_regressions(server, resolver, name, tmp_path):
    _, out = await _render(server, resolver, name, tmp_path)
    a11y = [f for f in out.findings if f.dimension == "accessibility" and f.severity != "minor"]
    assert not a11y, [f.issue for f in a11y]


async def test_deterministic_checks_catch_a_broken_layout(server, resolver, tmp_path):
    """A layout wider than a phone must be reported, not silently clipped. Components collapse on
    their own now, so the bad fix is simulated on the page layout the engine hands the renderer."""
    model = resolver.resolve(DesignSpec.model_validate(ALL["saas_landing"]))
    assert model.root.layout is not None
    for snapshot in (model.root.layout.props, *model.root.layout.responsive.values()):
        snapshot["minWidth"] = "1100px"
    out = await PlaywrightRenderer(server=server, screenshot_dir=tmp_path).render_with_findings(
        model
    )
    assert any(f.severity == "critical" and "mobile" in f.issue for f in out.findings)


async def test_reduced_motion_renders(server, resolver, tmp_path):
    _, out = await _render(server, resolver, "saas_landing", tmp_path, reduced_motion=True)
    assert not [f for f in out.findings if f.severity == "critical"]


async def test_unknown_implementation_is_a_structured_error(server, resolver, tmp_path):
    model = resolver.resolve(DesignSpec.model_validate(ALL["settings"]))
    model.root.children[0].implementation = "NotAComponent"
    out = await PlaywrightRenderer(server=server, screenshot_dir=tmp_path).render_with_findings(
        model
    )
    assert any("no implementation registered" in f.issue for f in out.findings)
