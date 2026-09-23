"""Phase 14 - Screenshot UI/UX Verifier. Looks at the rendered screen and reports what to fix."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

from PIL import Image

from app.agents.base import Agent
from app.core.exceptions import ValidationError
from app.core.llm import LLMProvider
from app.models.common import Dimension, Severity, StrictModel
from app.models.dsl import DesignSpec, SectionSpec
from app.models.render import RenderModel, RenderResult
from app.models.verification import Issue, VerificationResult
from app.recipes.registry import RecipeRegistry

SYSTEM = """You are a senior UI/UX reviewer. You look at a rendered screen and report only the
problems a user would actually see.

Evidence, in priority order: 1. the screenshots, 2. the deterministic findings, 3. the section
outline, 4. the screen's purpose. Screenshot-visible issues come first.

Check each breakpoint (mobile, tablet, desktop) for:
- layout: alignment, spacing, hierarchy, balance, overflow, clipping, responsive breakage
- visual: contrast, typography, consistency, density, hierarchy
- ux: missing actions, unclear states, confusing hierarchy
- accessibility: problems visible in the screenshot

The deterministic findings are already confirmed and will be fixed; do not repeat them.

Do not report invisible implementation details. The copy and photographs are the product's own
content: judge how they sit in the layout (overflow, clipping, text over imagery), never their
wording or choice of picture. Where a section still shows repeated sample items, those are
stand-ins by design. Judge structure, layout and visual design only, and do not invent problems.
Do not propose rewriting the screen.
Every issue targets one section id from the list below, or "page" if it spans the whole page.
Severity: critical = broken or unusable, major = clearly hurts the task, minor = polish.
An empty list is the right answer for a screen that works."""

USER = """Screen `{screen_id}` - recipe `{recipe}`: {purpose}

Sections, top to bottom. `target` is the id in backticks, nothing else:
{sections}

Deterministic findings (already confirmed):
{findings}

Screenshots follow, one per breakpoint."""


class VerifierIssue(StrictModel):
    severity: Severity
    dimension: Dimension
    target: str
    issue: str
    suggestion: str


class VerifierOutput(StrictModel):
    issues: list[VerifierIssue]


#: Only these make a screen fail. Minor issues are reported but never trigger a fix.
BLOCKING = {Severity.critical, Severity.major}


class VerifierAgent(Agent):
    """Satisfies app.services.interfaces.VerifierService."""

    name = "verifier"

    def __init__(self, llm: LLMProvider, recipes: RecipeRegistry) -> None:
        super().__init__(llm)
        self._recipes = recipes

    async def verify(
        self, spec: DesignSpec, model: RenderModel, result: RenderResult
    ) -> VerificationResult:
        targets = {"page", *_section_ids(spec.sections)}
        text = USER.format(
            screen_id=spec.screen_id,
            recipe=spec.recipe,
            purpose=self._recipes.get(spec.recipe).purpose,
            sections="\n".join(_section_lines(spec.sections)),
            findings="\n".join(
                f"- [{f.severity.value}] {f.target}: {f.issue}" for f in result.findings
            )
            or "(none)",
        )
        content: list[dict[str, Any]] = [{"type": "text", "text": text}]
        for bp, shot in result.screenshots.items():
            content.append({"type": "text", "text": f"{bp.value}:"})
            content.append({"type": "image_url", "image_url": {"url": _data_url(shot)}})

        out = await self._invoke(SYSTEM, content, VerifierOutput, lambda o: _validate(o, targets))
        issues = [
            *result.findings,
            *(Issue(**i.model_dump(), deterministic=False) for i in out.issues),
        ]
        blocking = any(i.severity in BLOCKING for i in issues)
        return VerificationResult(status="needs_fix" if blocking else "pass", issues=issues)


def _validate(out: VerifierOutput, targets: set[str]) -> VerifierOutput:
    unknown = sorted({i.target for i in out.issues} - targets)
    if unknown:
        raise ValidationError(
            f"unknown targets {unknown}; use one of {sorted(targets)}", target="issues"
        )
    return out


def _section_ids(sections: list[SectionSpec]) -> list[str]:
    return [i for s in sections for i in (s.id, *_section_ids(s.children))]


def _section_lines(sections: list[SectionSpec], depth: int = 0) -> list[str]:
    lines = []
    for s in sections:
        lines.append(f"{'  ' * depth}- `{s.id}` ({s.type}, {s.variant or 'default'} variant)")
        lines.extend(_section_lines(s.children, depth + 1))
    return lines


#: Vision models bill per 512px tile and scale the short side up to 768px. A full-page 2x
#: screenshot at 512px wide keeps layout legible at roughly a third of the tiles.
MAX_IMAGE_WIDTH = 512


def _data_url(shot: str) -> str:
    """The renderer returns a file path when it has a screenshot dir, base64 otherwise."""
    if len(shot) < 1024 and Path(shot).is_file():
        raw = Path(shot).read_bytes()
    else:
        raw = base64.b64decode(shot)
    return f"data:image/png;base64,{base64.b64encode(_downscale(raw)).decode()}"


def _downscale(png: bytes) -> bytes:
    image = Image.open(io.BytesIO(png))
    if image.width <= MAX_IMAGE_WIDTH:
        return png
    height = round(image.height * MAX_IMAGE_WIDTH / image.width)
    out = io.BytesIO()
    image.resize((MAX_IMAGE_WIDTH, height), Image.Resampling.LANCZOS).save(out, format="PNG")
    return out.getvalue()
