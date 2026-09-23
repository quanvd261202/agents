"""Phase 15 - Targeted Fixer. The smallest DSL patches that resolve the verifier's findings."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from app.agents.base import Agent
from app.agents.verifier import BLOCKING
from app.catalog.models import ComponentDefinition
from app.catalog.registry import ComponentRegistry
from app.core.exceptions import UIBuilderError, ValidationError
from app.core.llm import LLMProvider
from app.core.logging import get_logger
from app.dsl.resolver import DesignResolver
from app.learning.service import describe, signature
from app.models.common import Density, Severity, StrictModel
from app.models.dsl import AnimationIntent, DesignSpec, LayoutIntent, SectionSpec
from app.models.learning import Lesson
from app.models.verification import FixResult, Issue, Patch, VerificationResult
from app.recipes.registry import RecipeRegistry

log = get_logger(__name__)

Property = Literal["variant", "type", "animation", "layout", "columns", "remove", "density"]

SYSTEM = """You repair a screen described in a compact Design DSL. Apply the smallest set of patches
that resolves the listed issues. Never regenerate the page.

Each patch is {target, property, value}:
- variant: another variant of the section's component
- type: another component allowed in that section's slot
- animation: a motion the component supports, or "none"
- layout: a layout type the component supports
- columns: a column count 1-6, as a string
- remove: drop an optional section (value "true")
- density (target "page"): compact | comfortable | spacious

Use only the allowed values listed for each section; never invent ids or values. Touch only the
sections named by the issues. Fix in this order: critical layout problems, missing required
content, accessibility, responsive issues, visual hierarchy, polish.

If no allowed patch can resolve the issues, return status "failure" with the reason and no
patches."""

USER = """Screen `{screen_id}` (recipe `{recipe}`), density {density}.

Issues to fix, most important first:
{issues}

Sections you may patch, with their allowed values:
{sections}{lessons}"""

LESSONS = """

Lessons from earlier verified fixes on pages like this one; prefer them where they fit:
{lines}"""


class FixPatch(StrictModel):
    target: str
    property: Property
    value: str


class FixerOutput(StrictModel):
    status: Literal["success", "failure"]
    patches: list[FixPatch]
    reason: str | None


class FixerAgent(Agent):
    """Satisfies app.services.interfaces.FixerService."""

    name = "fixer"

    def __init__(
        self,
        llm: LLMProvider,
        recipes: RecipeRegistry,
        components: ComponentRegistry,
        resolver: DesignResolver,
    ) -> None:
        super().__init__(llm)
        self._recipes = recipes
        self._components = components
        self._resolver = resolver

    async def fix(
        self,
        spec: DesignSpec,
        verification: VerificationResult,
        lessons: Sequence[Lesson] = (),
    ) -> FixResult:
        issues = sorted(
            (i for i in verification.issues if i.severity in BLOCKING),
            key=lambda i: (i.severity != Severity.critical, not i.deterministic),
        )
        if (learned := self._from_lessons(spec, issues, lessons)) is not None:
            return learned
        allowed = self._patchable(spec, issues)
        out = await self._invoke(
            SYSTEM,
            USER.format(
                screen_id=spec.screen_id,
                recipe=spec.recipe,
                density=spec.density.value,
                issues="\n".join(
                    f"- [{i.severity.value}/{i.dimension.value}] {i.target}: {i.issue}"
                    f" (suggestion: {i.suggestion})"
                    for i in issues
                ),
                sections="\n".join(self._allowed_line(spec, s) for s in allowed),
                lessons=LESSONS.format(lines="\n".join(f"- {describe(x)}" for x in lessons))
                if lessons
                else "",
            ),
            FixerOutput,
            lambda o: self._validate(o, spec, {s.id for s in allowed}),
        )
        return _to_result(out)

    def _from_lessons(
        self, spec: DesignSpec, issues: list[Issue], lessons: Sequence[Lesson]
    ) -> FixResult | None:
        """Trusted lessons are applied without a model call when, together, they match every
        blocking issue (same component, same deterministic problem) and the patched spec still
        resolves. Anything less goes to the model, with the lessons as hints."""
        trusted = [x for x in lessons if x.status == "trusted"]
        if not trusted or not issues:
            return None
        patches: list[Patch] = []
        ids: set[str] = set()
        for issue in issues:
            section = spec.find(issue.target)
            if section is None or not issue.deterministic:
                return None
            match = next(
                (
                    x
                    for x in trusted
                    if x.scope.get("component") == section.type
                    and x.scope.get("problem") == signature(issue)
                ),
                None,
            )
            if match is None:
                return None
            patch = Patch(
                target=issue.target, property=match.fix["property"], value=match.fix["value"]
            )
            if patch not in patches:
                patches.append(patch)
            ids.add(match.id)
        fix = FixResult(
            status="success",
            patches=patches,
            reason="applied trusted lessons",
            source="lesson",
            lesson_ids=sorted(ids),
        )
        try:
            self._resolver.resolve(self.apply(spec, fix))
        except UIBuilderError as e:
            log.warning("fixer.lesson_rejected", error=str(e))
            return None
        log.info("fixer.from_lessons", screen=spec.screen_id, lessons=fix.lesson_ids)
        return fix

    # -------------------------------------------------------------------------------------
    def _patchable(self, spec: DesignSpec, issues: list[Issue]) -> list[SectionSpec]:
        """Only sections an issue names. A page-wide issue may be caused by any section."""
        targets = {i.target for i in issues}
        if targets & {"page", "main"}:
            return list(_walk(spec.sections))
        return [s for s in _walk(spec.sections) if s.id in targets]

    def _allowed_line(self, spec: DesignSpec, s: SectionSpec) -> str:
        comp = self._components.get(s.type)
        slot = self._recipes.get(spec.recipe).section(s.id)
        parts = [
            f"variant: {', '.join(comp.variants)}",
            f"animation: {', '.join(comp.animation_capabilities)}",
        ]
        if comp.supported_layouts:
            parts.append(f"layout: {', '.join(comp.supported_layouts)}")
        if slot is not None:
            parts.append(f"type: {', '.join(slot.component_types)}")
            parts.append("removable" if not slot.required else "required")
        current = f"{s.type}/{s.variant or comp.default_variant}"
        return f"- {s.id} (now {current}): " + "; ".join(parts)

    def _validate(self, out: FixerOutput, spec: DesignSpec, allowed: set[str]) -> FixerOutput:
        if out.status == "failure":
            if out.patches:
                raise ValidationError("status 'failure' must come with no patches")
            return out
        if not out.patches:
            raise ValidationError("status 'success' needs at least one patch")
        for p in out.patches:
            if p.property == "density":
                if p.target != "page":
                    raise ValidationError("density patches target 'page'", target=p.target)
            elif p.target not in allowed:
                raise ValidationError(
                    f"'{p.target}' is not named by any issue; patch only {sorted(allowed)}",
                    target=p.target,
                )
        # The deterministic resolver is the judge: a patch that does not resolve is not a fix.
        try:
            self._resolver.resolve(self.apply(spec, _to_result(out)))
        except UIBuilderError as e:
            raise ValidationError(f"the patched spec does not resolve: {e}") from e
        return out

    def apply(self, spec: DesignSpec, fix: FixResult) -> DesignSpec:
        """Deterministic. Applies patches in order; untouched sections are left exactly as-is."""
        for p in fix.patches:
            value = str(p.value)
            if p.property == "density":
                try:
                    spec = spec.model_copy(update={"density": Density(value)})
                except ValueError as e:
                    raise ValidationError(f"unknown density '{value}'", target="page") from e
                continue
            if spec.find(p.target) is None:
                raise ValidationError(f"no section '{p.target}'", target=p.target)
            layout_default = self._slot_layout(spec, p.target)
            sections = _patch(spec.sections, p.target, p.property, value, spec, layout_default)
            if p.property == "type":
                sections = _prune(sections, p.target, self._components.get(value))
            spec = spec.model_copy(update={"sections": sections})
        return spec

    def _slot_layout(self, spec: DesignSpec, section_id: str) -> str:
        slot = self._recipes.get(spec.recipe).section(section_id)
        return slot.layout.value if slot is not None and slot.layout is not None else "grid"


def _to_result(out: FixerOutput) -> FixResult:
    return FixResult(
        status=out.status,
        patches=[Patch(target=p.target, property=p.property, value=p.value) for p in out.patches],
        reason=out.reason,
    )


def _walk(sections: list[SectionSpec]) -> list[SectionSpec]:
    return [x for s in sections for x in (s, *_walk(s.children))]


def _prune(
    sections: list[SectionSpec], target: str, comp: ComponentDefinition
) -> list[SectionSpec]:
    """A section that changed component keeps only the copy, photographs and product cards its
    new component can show; the rest would make the patched spec unresolvable."""
    out: list[SectionSpec] = []
    for s in sections:
        if s.id == target:
            slots = comp.slot_names()
            s = s.model_copy(
                update={
                    "content": {k: v for k, v in s.content.items() if k in slots},
                    "images": {k: v for k, v in s.images.items() if k in slots},
                    "children": [c for c in s.children if c.type in comp.allowed_children],
                }
            )
        elif s.children:
            s = s.model_copy(update={"children": _prune(s.children, target, comp)})
        out.append(s)
    return out


def _patch(
    sections: list[SectionSpec],
    target: str,
    prop: str,
    value: str,
    spec: DesignSpec,
    layout_default: str,
) -> list[SectionSpec]:
    out: list[SectionSpec] = []
    for s in sections:
        if s.id != target:
            children = _patch(s.children, target, prop, value, spec, layout_default)
            out.append(s if children == s.children else s.model_copy(update={"children": children}))
            continue
        if prop == "remove":
            continue
        if prop == "variant":
            s = s.model_copy(update={"variant": value})
        elif prop == "type":
            s = s.model_copy(update={"type": value, "variant": None, "animation": None})
        elif prop == "animation":
            intensity = (s.animation or spec.animation or AnimationIntent(name="none")).intensity
            s = s.model_copy(update={"animation": AnimationIntent(name=value, intensity=intensity)})
        elif prop == "layout":
            layout = (s.layout or LayoutIntent(type=value)).model_copy(update={"type": value})
            s = s.model_copy(update={"layout": layout})
        elif prop == "columns":
            if not value.isdigit() or not 1 <= int(value) <= 6:
                raise ValidationError(f"columns must be 1-6, got '{value}'", target=target)
            layout = s.layout or LayoutIntent(type=layout_default)
            s = s.model_copy(update={"layout": layout.model_copy(update={"columns": int(value)})})
        out.append(s)
    return out
