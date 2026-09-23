"""Phase 08 - UX Planner. Turns clarified requirements into a UX-level plan."""

from __future__ import annotations

from app.agents.base import Agent, brief_block
from app.core.exceptions import ValidationError
from app.core.llm import LLMProvider
from app.models.plan import UXPlan
from app.models.requirements import ClarifiedRequirements
from app.recipes.registry import RecipeRegistry

SYSTEM = """You are a UX planner. You decide what the product's screens are and why they exist.

Decide: user goals, the primary journey, information architecture, which screens are needed,
each screen's purpose, its key content, and its required interactions.

You MUST NOT decide: CSS, spacing, colors, coordinates, component names, layout structure,
or animation. Those belong to later agents.

Keep it compact. Only screens the journey actually needs - no speculative screens. Screen ids are
lowercase snake_case and unique. Order `screens` along the journey, most important first.

Only these kinds of page can be built for this product: {page_types}. Every screen must be one of
them; a screen that fits none cannot be built, so leave it out rather than stretch a page type.

When the user's brief is given it is the source of truth, over the summary above it. Every page it
describes gets a screen, and that screen's `key_content` and `interactions` carry what the brief
asks for on it, as short phrases in the brief's own terms. Leave out what no page type can hold."""

USER = """Product: {product}
Domain: {domain}
Audience: {audience}
Primary goal: {goal}
Key features: {features}
Constraints: {constraints}{brief}"""


class PlannerAgent(Agent):
    """Satisfies app.services.interfaces.PlannerService."""

    name = "planner"

    def __init__(self, llm: LLMProvider, recipes: RecipeRegistry) -> None:
        super().__init__(llm)
        self._recipes = recipes

    async def plan(self, req: ClarifiedRequirements, brief: str = "") -> UXPlan:
        page_types = sorted({r.page_type for r in self._recipes.for_domain(req.domain)})
        return await self._invoke(
            SYSTEM.format(page_types=", ".join(page_types)),
            USER.format(
                product=req.product,
                domain=req.domain,
                audience=req.target_audience,
                goal=req.primary_goal,
                features=", ".join(req.key_features) or "(none stated)",
                constraints=", ".join(req.constraints) or "(none stated)",
                brief=brief_block(brief),
            ),
            UXPlan,
            self._validate,
        )

    @staticmethod
    def _validate(plan: UXPlan) -> UXPlan:
        ids = [s.id for s in plan.screens]
        if len(ids) != len(set(ids)):
            raise ValidationError(f"duplicate screen ids: {ids}")
        return plan
