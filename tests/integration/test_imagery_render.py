"""Real photographs in the browser: an image slot with a sourced URL renders the picture, a slot
without one keeps the placeholder, and the checks stay clean. Uses inline SVG data URLs so the
suite needs no network. Skipped when the bundle or playwright is absent."""

from __future__ import annotations

import re
from urllib.parse import quote

import pytest

from app.dsl import default_design_resolver
from app.models import DesignSpec, ImageRef
from app.renderer import PlaywrightRenderer, StaticServer
from app.renderer.server import FRONTEND_DIST

pytest.importorskip("playwright.async_api")
pytestmark = [
    pytest.mark.skipif(
        not (FRONTEND_DIST / "index.html").exists(), reason="frontend bundle not built"
    ),
    pytest.mark.integration,
]


def photo(fill: str) -> ImageRef:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='800' height='600'>"
        f"<rect width='800' height='600' fill='{fill}'/></svg>"
    )
    return ImageRef(url="data:image/svg+xml;utf8," + quote(svg), alt="test photo", credit="test")


def card(i: int, with_photo: bool) -> dict[str, object]:
    return {
        "id": f"featured_products-item-{i}",
        "type": "product_card",
        "content": {
            "image": "bag of roasted coffee beans",
            "title": f"Roast No. {i}",
            "note": "Chocolate and cherry",
            "price": "$18",
            **({"badge": "New"} if i == 1 else {}),
        },
        **({"images": {"image": [photo("#b5651d")]}} if with_photo else {}),
    }


SPEC = DesignSpec(
    screen_id="home",
    recipe="ecommerce_home",
    visual_style="warm_editorial",
    theme="premium_light",
    palette="espresso",
    sections=[
        {"id": "navigation", "type": "navigation"},
        {
            "id": "hero",
            "type": "hero",
            "content": {
                "headline": "Coffee worth waking for",
                "subhead": "Roasted weekly, shipped the same day.",
                "media": "pour-over coffee on a sunlit oak counter",
            },
            "images": {"media": [photo("#7a4a2a")]},
        },
        {
            "id": "collections",
            "type": "collection_grid",
            "content": {
                "collections": "Beans,Tea,Gear",
                "media": "coffee beans in a scoop, loose leaf tea, ceramic pour-over",
            },
            # the second tile found nothing: its position keeps the placeholder
            "images": {"media": [photo("#333"), ImageRef(url=""), photo("#666")]},
        },
        {
            "id": "featured_products",
            "type": "product_grid",
            "variant": "premium",
            "content": {"title": "This week's roasts"},
            "children": [card(1, True), card(2, True), card(3, False)],
        },
        {"id": "footer", "type": "footer"},
    ],
)


async def test_sourced_photographs_render_and_placeholders_fill_the_gaps(tmp_path):
    model = default_design_resolver().resolve(SPEC)
    with StaticServer() as server:
        out = await PlaywrightRenderer(server=server, screenshot_dir=tmp_path).render_with_findings(
            model
        )
    html = out.result.html or ""
    # hero + two collection tiles + two cards with photos = 5 pictures; the rest are placeholders
    assert len(re.findall(r"<img[^>]+src=\"data:image/svg\+xml", html)) == 5
    assert "Roast No. 3" in html and "Roast No. 1" in html  # real product copy, not the samples
    assert "Nº1 Signature" not in html
    assert "Coffee worth waking for" in html

    blocking = [
        f
        for f in out.findings
        if f.severity == "critical" or (f.severity == "major" and f.dimension == "accessibility")
    ]
    assert not blocking, [f.issue for f in blocking]
