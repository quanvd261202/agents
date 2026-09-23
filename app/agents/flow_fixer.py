"""M13 - Flow Fixer. Repairs the site plan when the flow check finds a dead control or a journey
step that does not arrive.

Rules come first: a control whose intent the screen never links gets the edge when the plan has
a screen of that kind, with no model call. Only when no rule applies is the model asked, and it
may only propose patches (add_edge, retarget_edge, set_route): the plan is replaced by the
validated result of applying them, never edited freely. It never adds a screen."""

from __future__ import annotations

from typing import Literal

from app.agents.base import Agent
from app.catalog.registry import ComponentRegistry
from app.core.exceptions import ValidationError
from app.core.llm import LLMProvider
from app.flow.intents import IntentRegistry, default_intent_registry
from app.flow.repair import apply_patches, rule_patches
from app.models.common import StrictModel
from app.models.direction import DesignDirection
from app.models.flow import FlowFixResult, FlowReport, SitePlanPatch
from app.models.plan import UXPlan
from app.recipes.registry import RecipeRegistry

SYSTEM = """You repair the site plan of a product: which screens link to which, by intent. The site
was opened in a browser and some journeys did not arrive, or some controls lead nowhere.

Return the smallest set of patches. Each patch is one of:
- add_edge {screen, intent, to}: the screen gains a link
- retarget_edge {screen, intent, to}: the screen's existing link with that intent now points at `to`
- set_route {screen, route}: the screen's URL path changes

Only planned screens, only intents from the vocabulary, and a link's target must be the kind of
page the intent means (a cart for view_cart, a product_detail for open_item). You cannot add
screens: a failure that needs a page the plan lacks is not yours to fix - return status
"failure" with the reason and no patches."""

USER = """Screens (id, route, page type, links):
{screens}

Intents:
{intents}

Failures:
{failures}"""


class FlowFixerOutput(StrictModel):
    status: Literal["success", "failure"]
    patches: list[SitePlanPatch]
    reason: str | None


class FlowFixerAgent(Agent):
    """Satisfies app.services.interfaces.FlowFixerService."""

    name = "flow_fixer"

    def __init__(
        self,
        llm: LLMProvider,
        recipes: RecipeRegistry,
        components: ComponentRegistry,
        intents: IntentRegistry | None = None,
    ) -> None:
        super().__init__(llm)
        self._recipes = recipes
        self._components = components
        self._intents = intents or default_intent_registry()

    async def fix(
        self, plan: UXPlan, report: FlowReport, direction: DesignDirection
    ) -> FlowFixResult:
        rules = rule_patches(
            plan, report, direction, self._recipes, self._components, self._intents
        )
        if rules:
            try:
                apply_patches(plan, rules, self._intents, direction, self._recipes)
                return FlowFixResult(status="success", patches=rules, source="rule")
            except ValidationError:
                pass  # a rule that does not hold up falls through to the model
        failures = [
            f"- journey {s.screen} --{s.intent}--> {s.to}: {s.detail}"
            for s in report.failed_steps()
        ] + [
            f"- dead control on '{d.screen}': {d.section} {d.role} ({d.text!r})"
            for d in report.dead
        ]
        if not failures:
            return FlowFixResult(status="failure", reason="nothing to fix", source="rule")
        page_type = {
            s.id: self._recipes.get(direction.recipe_for(s.id)).page_type for s in plan.screens
        }
        out = await self._invoke(
            SYSTEM,
            USER.format(
                screens="\n".join(
                    f"- {s.id} ({s.route}, {page_type[s.id]}): "
                    + (", ".join(f"{link.intent} -> {link.to}" for link in s.links) or "no links")
                    for s in plan.screens
                ),
                intents=self._intents.describe(),
                failures="\n".join(failures),
            ),
            FlowFixerOutput,
            lambda o: self._validate(o, plan, direction),
        )
        return FlowFixResult(
            status=out.status, patches=out.patches, reason=out.reason, source="model"
        )

    def _validate(
        self, out: FlowFixerOutput, plan: UXPlan, direction: DesignDirection
    ) -> FlowFixerOutput:
        if out.status == "success":
            if not out.patches:
                raise ValidationError("success needs at least one patch", target="patches")
            apply_patches(plan, out.patches, self._intents, direction, self._recipes)
        return out

    def apply(self, plan: UXPlan, fix: FlowFixResult) -> UXPlan:
        """Deterministic: the validated plan with the patches applied."""
        return apply_patches(plan, fix.patches, self._intents)
