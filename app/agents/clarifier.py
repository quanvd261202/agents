"""Phase 07 - Clarifier. Clarifies requirements and nothing else."""

from __future__ import annotations

import json

from app.agents.base import Agent
from app.core.exceptions import ValidationError
from app.core.llm import LLMProvider
from app.models.requirements import ClarifierOutput
from app.recipes.registry import RecipeRegistry

SYSTEM = """You clarify what a user wants built. You do NOT design anything.

You MUST NOT: plan screens, choose components, invent layouts, pick colors or styles, or produce
any UI. Later agents do all of that.

You may ask at most {max_questions} questions, and only ones whose answer would change the
product itself (who it is for, what it must do, hard constraints). Anything a sensible default
covers is an assumption, not a question - record it in `assumptions`. If you would pick the
default with confidence, do not ask. Never ask a catch-all ("any constraints?", "any other
requirements?") or about a goal the product type already implies (a shop sells). Most requirements
need zero or one question.

`key_features` are what the user asked for, in their terms; never add features they did not
mention (accounts, blogs, support channels). Your own guesses belong in `assumptions`.

Return status "needs_clarification" with the questions when something essential is missing.
Otherwise return status "ready" with `clarified_requirements` filled in. Once the user has
answered, prefer "ready": never ask a second round for polish.

Every question needs 2-4 concrete options and a `default`.

`domain` must be exactly one of: {domains}. Pick the closest one - it decides which page recipes
and components the later agents are even allowed to use."""

USER = """Requirement:
{requirement}

Answers already given by the user:
{answers}"""


class ClarifierAgent(Agent):
    """Satisfies app.services.interfaces.ClarifierService."""

    name = "clarifier"

    def __init__(self, llm: LLMProvider, recipes: RecipeRegistry, max_questions: int = 3) -> None:
        super().__init__(llm)
        self._max_questions = max_questions
        #: The recipes define which domains the rest of the pipeline can actually serve.
        self._domains = sorted({d for r in recipes for d in r.domains if d != "*"})

    async def clarify(self, requirement: str, answers: dict[str, str]) -> ClarifierOutput:
        return await self._invoke(
            SYSTEM.format(max_questions=self._max_questions, domains=", ".join(self._domains)),
            USER.format(
                requirement=requirement,
                answers=json.dumps(answers, ensure_ascii=False) if answers else "(none yet)",
            ),
            ClarifierOutput,
            lambda out: self._validate(out, answers),
        )

    def _validate(self, out: ClarifierOutput, answers: dict[str, str]) -> ClarifierOutput:
        if answers and out.status == "needs_clarification":
            raise ValidationError(
                "the user has already answered; return status 'ready' and fill the gaps with "
                "assumptions instead of asking again"
            )
        if out.status == "ready" and out.clarified_requirements is None:
            raise ValidationError("status 'ready' requires clarified_requirements")
        req = out.clarified_requirements
        if req is not None and req.domain not in self._domains:
            raise ValidationError(
                f"domain '{req.domain}'; it must be one of: {self._domains}", target="domain"
            )
        if out.status == "needs_clarification" and not out.questions:
            raise ValidationError("status 'needs_clarification' requires at least one question")
        if len(out.questions) > self._max_questions:
            raise ValidationError(f"at most {self._max_questions} questions are allowed")
        return out
