"""M6/M7 exit criteria, checked in a real browser.

M6: the same page under different brand axes (palette x typography x radius) must look like
different brands and stay WCAG AA. M7: every component x variant renders cleanly under a light and
a dark brand. Skipped when the bundle or playwright is absent.
"""

from __future__ import annotations

import hashlib

import pytest

from app.catalog import default_component_registry
from app.dsl import default_design_resolver
from app.models import DesignSpec
from app.models.common import Breakpoint
from app.models.dsl import SectionSpec
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

BRANDS = [
    ("espresso", "editorial_serif", "large"),
    ("midnight", "geometric", "medium"),
    ("citrus", "grotesk_display", "full"),
    ("noir", "luxe_serif", "none"),
    ("sage", "humanist", "small"),
]


@pytest.fixture(scope="module")
def server():
    with StaticServer() as s:
        yield s


def _blocking(findings):
    return [
        f
        for f in findings
        if f.severity == "critical" or (f.severity == "major" and f.dimension == "accessibility")
    ]


async def test_one_page_reads_as_five_brands_and_stays_accessible(server, tmp_path):
    resolver = default_design_resolver()
    renderer = PlaywrightRenderer([Breakpoint.desktop], server=server, screenshot_dir=tmp_path)
    fingerprints = set()
    for palette, typography, radius in BRANDS:
        spec = DesignSpec.model_validate(
            {
                **ALL["ecommerce_home"],
                "screen_id": palette,
                "palette": palette,
                "typography": typography,
                "radius": radius,
            }
        )
        out = await renderer.render_with_findings(resolver.resolve(spec))
        assert not _blocking(out.findings), (palette, [f.issue for f in _blocking(out.findings)])
        shot = (tmp_path / f"{palette}.desktop.png").read_bytes()
        fingerprints.add(hashlib.sha256(shot).hexdigest())
    assert len(fingerprints) == len(BRANDS)  # no two brands render identically


@pytest.mark.parametrize(("palette", "typography", "radius"), [BRANDS[0], BRANDS[1]])
async def test_every_component_variant_renders_cleanly(
    server, tmp_path, palette, typography, radius
):
    resolver = default_design_resolver()
    renderer = PlaywrightRenderer(server=server, screenshot_dir=tmp_path)
    failures = {}
    for comp in default_component_registry():
        model = resolver.preview(
            [SectionSpec(id=f"{comp.id}-{v}", type=comp.id, variant=v) for v in comp.variants],
            screen_id=comp.id,
            palette=palette,
            typography=typography,
            radius=radius,
        )
        bad = _blocking((await renderer.render_with_findings(model)).findings)
        if bad:
            failures[comp.id] = [f"{f.target}: {f.issue}" for f in bad]
    assert not failures, failures
