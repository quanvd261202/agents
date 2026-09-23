"""Phase 16 - Learning. Reusable design rules mined from verified fixes.

A lesson is deterministic all the way through: its scope is registry ids (domain, page type,
component), its problem is the normalised text of a deterministic check or an issue dimension,
and its fix is the patch that made the problem disappear. Nothing a user or a model wrote is ever
stored, so a shared store cannot leak tenant data. Lessons are advice until confirmed repeatedly:
candidates are never shown to an agent, validated ones are shown as hints, and only trusted ones
may be applied without a model call, and even then the deterministic resolver still decides."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime

from app.core.logging import get_logger
from app.models.direction import DesignDirection
from app.models.dsl import DesignSpec
from app.models.learning import LearningEvent, Lesson, LessonStatus
from app.models.requirements import ClarifiedRequirements
from app.models.verification import FixResult, Issue, Patch, VerificationResult
from app.recipes.registry import RecipeRegistry
from app.services.repositories import LessonRepository

log = get_logger(__name__)

#: Confirmations needed before a lesson is shown to agents, and before it may be applied.
VALIDATED_AT = 2
TRUSTED_AT = 3
#: Only these make a screen fail, so only these are worth learning from.
BLOCKING = {"critical", "major"}
_EVIDENCE_KEPT = 10
_BREAKPOINT = re.compile(r"^\[[a-z]+\]\s*")
_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def signature(issue: Issue) -> str:
    """The problem an issue reports, freed of what varies between screens. A deterministic
    check's text is stable up to breakpoint and measurements; a model's wording is not, so
    those issues are known only by dimension."""
    if not issue.deterministic:
        return f"{issue.dimension.value} issue"
    text = _BREAKPOINT.sub("", issue.issue)
    return _NUMBER.sub("N", text).strip()


def lesson_id(scope: dict[str, str], fix: dict[str, str]) -> str:
    key = json.dumps({"scope": scope, "fix": fix}, sort_keys=True)
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def status_for(confirmations: int, violations: int) -> LessonStatus:
    """Repeated confirmation promotes; a violation record that rivals the confirmations demotes."""
    if violations and violations * 2 >= confirmations:
        return "candidate"
    if confirmations >= TRUSTED_AT:
        return "trusted"
    if confirmations >= VALIDATED_AT:
        return "validated"
    return "candidate"


def describe(lesson: Lesson) -> str:
    return f"{lesson.text} [{lesson.status}, confirmed {lesson.confirmations}x]"


class LearningService:
    """Satisfies app.services.interfaces.LearningService."""

    def __init__(
        self, repository: LessonRepository, recipes: RecipeRegistry, *, max_lessons: int = 5
    ) -> None:
        self._repository = repository
        self._recipes = recipes
        self._max = max_lessons

    def _page_type(self, recipe_id: str) -> str:
        return self._recipes.get(recipe_id).page_type

    # --- into the agents -----------------------------------------------------------------------
    async def advise(
        self, req: ClarifiedRequirements, direction: DesignDirection, recipe: str
    ) -> list[str]:
        """Confirmed lessons for this kind of page, as one line each for the Design Builder."""
        scope = {"domain": req.domain, "page_type": self._page_type(recipe)}
        found = await self._repository.search(
            f"{recipe.replace('_', ' ')} {direction.visual_style.replace('_', ' ')}",
            scope,
            self._max * 2,
        )
        return [describe(x) for x in found if x.status != "candidate"][: self._max]

    async def suggest(
        self, spec: DesignSpec, verification: VerificationResult, domain: str
    ) -> list[Lesson]:
        """Confirmed lessons about the components and problems the verifier just reported."""
        page_type = self._page_type(spec.recipe)
        out: dict[str, Lesson] = {}
        for issue in verification.issues:
            section = spec.find(issue.target)
            if issue.severity.value not in BLOCKING or section is None:
                continue
            scope = {
                "domain": domain,
                "page_type": page_type,
                "component": section.type,
                "problem": signature(issue),
            }
            for lesson in await self._repository.search(issue.issue, scope, self._max):
                if lesson.status != "candidate":
                    out.setdefault(lesson.id, lesson)
        return list(out.values())

    # --- from the fix loop ---------------------------------------------------------------------
    async def learn(
        self,
        before: VerificationResult,
        fix: FixResult,
        after: VerificationResult,
        spec: DesignSpec,
        domain: str,
        run_id: str = "",
    ) -> list[LearningEvent]:
        """Compare the verification before and after a fix: each blocking issue a patch targeted
        either disappeared (the lesson is confirmed) or is still there (the lesson is violated)."""
        if fix.status != "success":
            return []
        page_type = self._page_type(spec.recipe)
        remaining = {(i.target, signature(i)) for i in after.issues if i.severity.value in BLOCKING}
        now = datetime.now(UTC)
        events: list[LearningEvent] = []
        for patch in fix.patches:
            value = _patch_value(patch)
            section = spec.find(patch.target)
            if value is None or section is None:
                continue  # page-level patches and structured values carry no reusable rule
            for issue in before.issues:
                if issue.target != patch.target or issue.severity.value not in BLOCKING:
                    continue
                problem = signature(issue)
                resolved = (issue.target, problem) not in remaining
                scope = {
                    "domain": domain,
                    "page_type": page_type,
                    "component": section.type,
                    "problem": problem,
                }
                events.append(
                    LearningEvent(
                        kind="fix_verified" if resolved else "fix_failed",
                        target=patch.target,
                        problem=problem,
                        fix=f"{patch.property}={value}",
                        occurred_at=now,
                        context=scope,
                    )
                )
                await self._record(
                    scope, {"property": patch.property, "value": value}, resolved, run_id
                )
        for lid in fix.lesson_ids:
            events.append(
                LearningEvent(kind="lesson_applied", target=lid, problem="", occurred_at=now)
            )
        return events

    async def _record(
        self, scope: dict[str, str], fix: dict[str, str], confirmed: bool, run_id: str
    ) -> Lesson:
        lid = lesson_id(scope, fix)
        lesson = await self._repository.get(lid) or Lesson(
            id=lid, text=_text(scope, fix), scope=scope, fix=fix
        )
        confirmations = lesson.confirmations + (1 if confirmed else 0)
        violations = lesson.violations + (0 if confirmed else 1)
        evidence = [*lesson.evidence, run_id][-_EVIDENCE_KEPT:] if run_id else lesson.evidence
        lesson = lesson.model_copy(
            update={
                "confirmations": confirmations,
                "violations": violations,
                "status": status_for(confirmations, violations),
                "evidence": evidence,
            }
        )
        await self._repository.upsert(lesson)
        log.info("learning.lesson", id=lid, status=lesson.status, confirmed=confirmed)
        return lesson


def _patch_value(patch: Patch) -> str | None:
    return str(patch.value) if isinstance(patch.value, str | int) else None


def _text(scope: dict[str, str], fix: dict[str, str]) -> str:
    return (
        f"{scope['component']} on {scope['page_type']} pages ({scope['domain']}): "
        f"'{scope['problem']}' was fixed by {fix['property']}={fix['value']}"
    )
