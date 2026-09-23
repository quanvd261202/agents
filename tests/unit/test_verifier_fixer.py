"""Phase 14-15 agents against a scripted provider: no network, no browser."""

from __future__ import annotations

import base64
import io

import pytest
from PIL import Image

from app.agents import FixerAgent, VerifierAgent
from app.agents.fixer import FixerOutput
from app.agents.verifier import VerifierOutput
from app.catalog import default_component_registry
from app.core.exceptions import ValidationError
from app.core.llm import FakeLLMProvider
from app.dsl import default_design_resolver
from app.models import DesignSpec, FixResult, Issue, Patch, RenderResult, VerificationResult
from app.models.common import Breakpoint, Density
from app.recipes import default_recipe_registry
from tests.fixtures.specs import ALL

CART = DesignSpec.model_validate(ALL["ecommerce_cart"])
MODEL = default_design_resolver().resolve(CART)


def png(width: int, height: int) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(out, format="PNG")
    return out.getvalue()


SMALL = base64.b64encode(png(100, 200)).decode()
SHOTS = {Breakpoint.mobile: SMALL, Breakpoint.desktop: SMALL}


def issue(target: str, severity: str = "major", deterministic: bool = False) -> Issue:
    return Issue(
        severity=severity,
        dimension="layout",
        target=target,
        issue="x",
        suggestion="y",
        deterministic=deterministic,
    )


def llm_issue(target: str, severity: str = "major") -> dict[str, str]:
    return {
        "severity": severity,
        "dimension": "visual",
        "target": target,
        "issue": "x",
        "suggestion": "y",
    }


# --- Phase 14 ------------------------------------------------------------------------------
async def verify(*responses: VerifierOutput, findings: list[Issue] | None = None):
    llm = FakeLLMProvider(list(responses))
    result = RenderResult(screenshots=SHOTS, findings=findings or [])
    return await VerifierAgent(llm, default_recipe_registry()).verify(CART, MODEL, result), llm


async def test_a_clean_screen_passes():
    v, _ = await verify(VerifierOutput(issues=[]))
    assert v == VerificationResult(status="pass")


async def test_deterministic_findings_fail_the_screen_whatever_the_model_says():
    finding = issue("cart_items", "critical", deterministic=True)
    v, llm = await verify(VerifierOutput(issues=[]), findings=[finding])
    assert v.status == "needs_fix"
    assert v.issues == [finding]
    assert "cart_items: x" in llm.calls[0][1].content[0]["text"]  # shown as already confirmed


async def test_minor_issues_are_reported_but_do_not_fail():
    v, _ = await verify(VerifierOutput(issues=[llm_issue("footer", "minor")]))
    assert v.status == "pass"
    assert [i.target for i in v.issues] == ["footer"]
    assert v.issues[0].deterministic is False


async def test_a_major_visual_issue_fails():
    v, _ = await verify(VerifierOutput(issues=[llm_issue("order_summary")]))
    assert v.status == "needs_fix"


async def test_every_breakpoint_screenshot_is_sent_as_an_image():
    _, llm = await verify(VerifierOutput(issues=[]))
    images = [b["image_url"]["url"] for b in llm.calls[0][1].content if b["type"] == "image_url"]
    assert images == [f"data:image/png;base64,{s}" for s in SHOTS.values()]


async def test_screenshot_paths_are_read_from_disk(tmp_path):
    shot = tmp_path / "cart.mobile.png"
    shot.write_bytes(png(100, 200))
    llm = FakeLLMProvider([VerifierOutput(issues=[])])
    result = RenderResult(screenshots={Breakpoint.mobile: str(shot)})
    await VerifierAgent(llm, default_recipe_registry()).verify(CART, MODEL, result)
    [image] = [b for b in llm.calls[0][1].content if b["type"] == "image_url"]
    assert image["image_url"]["url"] == f"data:image/png;base64,{SMALL}"


async def test_wide_screenshots_are_downscaled_before_sending():
    llm = FakeLLMProvider([VerifierOutput(issues=[])])
    wide = base64.b64encode(png(2560, 4000)).decode()
    result = RenderResult(screenshots={Breakpoint.desktop: wide})
    await VerifierAgent(llm, default_recipe_registry()).verify(CART, MODEL, result)
    [image] = [b for b in llm.calls[0][1].content if b["type"] == "image_url"]
    sent = Image.open(io.BytesIO(base64.b64decode(image["image_url"]["url"].split(",", 1)[1])))
    assert sent.size == (512, 800)


async def test_an_invented_target_is_sent_back_for_repair():
    v, llm = await verify(
        VerifierOutput(issues=[llm_issue("hero_banner")]),
        VerifierOutput(issues=[llm_issue("cart_items")]),
    )
    assert [i.target for i in v.issues] == ["cart_items"]
    assert "hero_banner" in llm.calls[1][-1].content


# --- Phase 15: apply -----------------------------------------------------------------------
def fixer(*responses: FixerOutput) -> FixerAgent:
    return FixerAgent(
        FakeLLMProvider(list(responses)),
        default_recipe_registry(),
        default_component_registry(),
        default_design_resolver(),
    )


def apply(*patches: tuple[str, str, str]) -> DesignSpec:
    fix = FixResult(
        status="success", patches=[Patch(target=t, property=p, value=v) for t, p, v in patches]
    )
    return fixer().apply(CART, fix)


def test_apply_changes_only_the_target():
    spec = apply(("cross_sell", "variant", "carousel"))
    assert spec.find("cross_sell").variant == "carousel"
    untouched = [s for s in spec.sections if s.id != "cross_sell"]
    assert untouched == [s for s in CART.sections if s.id != "cross_sell"]


def test_apply_type_change_drops_the_old_variant():
    spec = fixer().apply(
        DesignSpec.model_validate(ALL["ecommerce_home"]),
        FixResult(
            status="success",
            patches=[Patch(target="testimonials", property="type", value="testimonial_grid")],
        ),
    )
    section = spec.find("testimonials")
    assert (section.type, section.variant, section.animation) == ("testimonial_grid", None, None)


def test_apply_columns_uses_the_recipe_slot_layout():
    spec = fixer().apply(
        DesignSpec.model_validate(ALL["ecommerce_listing"]),
        FixResult(
            status="success", patches=[Patch(target="product_grid", property="columns", value="2")]
        ),
    )
    layout = spec.find("product_grid").layout
    assert (layout.type, layout.columns) == ("grid", 2)


def test_apply_remove_and_density():
    spec = apply(("cross_sell", "remove", "true"), ("page", "density", "compact"))
    assert spec.find("cross_sell") is None
    assert spec.density == Density.compact


# --- Phase 15: fix -------------------------------------------------------------------------
NEEDS_FIX = VerificationResult(
    status="needs_fix", issues=[issue("cross_sell"), issue("footer", "minor")]
)


def patch(target: str, prop: str, value: str) -> FixerOutput:
    return FixerOutput(
        status="success",
        patches=[{"target": target, "property": prop, "value": value}],
        reason=None,
    )


async def test_fix_returns_the_patch():
    fix = await fixer(patch("cross_sell", "variant", "carousel")).fix(CART, NEEDS_FIX)
    assert fix == FixResult(
        status="success", patches=[Patch(target="cross_sell", property="variant", value="carousel")]
    )


async def test_fixer_sees_only_blocking_issues_and_their_sections():
    agent = fixer(patch("cross_sell", "variant", "carousel"))
    await agent.fix(CART, NEEDS_FIX)
    user = agent._llm.calls[0][1].content  # type: ignore[attr-defined]
    assert "- cross_sell (now related_products/grid): variant: carousel, grid" in user
    assert "footer" not in user  # minor issue: neither listed nor patchable


async def test_fixer_may_not_touch_a_section_no_issue_names():
    agent = fixer(
        patch("navigation", "variant", "minimal"), patch("cross_sell", "variant", "carousel")
    )
    fix = await agent.fix(CART, NEEDS_FIX)
    assert fix.patches[0].target == "cross_sell"
    assert "not named by any issue" in agent._llm.calls[1][-1].content  # type: ignore[attr-defined]


async def test_a_patch_the_resolver_rejects_is_repaired():
    agent = fixer(
        patch("cross_sell", "variant", "holographic"), patch("cross_sell", "variant", "carousel")
    )
    fix = await agent.fix(CART, NEEDS_FIX)
    assert fix.patches[0].value == "carousel"
    assert "does not resolve" in agent._llm.calls[1][-1].content  # type: ignore[attr-defined]


async def test_removing_a_required_section_is_rejected():
    required = VerificationResult(status="needs_fix", issues=[issue("cart_items")])
    bad = patch("cart_items", "remove", "true")
    with pytest.raises(ValidationError, match="does not resolve"):
        await fixer(bad, bad, bad).fix(CART, required)


async def test_a_page_wide_issue_opens_every_section():
    page = VerificationResult(status="needs_fix", issues=[issue("page", "critical", True)])
    fix = await fixer(patch("cross_sell", "columns", "2")).fix(CART, page)
    assert fix.patches[0].target == "cross_sell"


async def test_the_fixer_may_give_up():
    out = FixerOutput(status="failure", patches=[], reason="needs a new component")
    fix = await fixer(out).fix(CART, NEEDS_FIX)
    assert (fix.status, fix.reason) == ("failure", "needs a new component")
