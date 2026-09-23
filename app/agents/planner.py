"""Phase 08 - UX Planner. Turns clarified requirements into a UX-level plan: the screens, and
(M13) how they connect - routes, links as intents, and the primary journey."""

from __future__ import annotations

from app.agents.base import Agent, brief_block
from app.core.llm import LLMProvider
from app.flow import IntentRegistry, default_intent_registry, normalise_routes, validate_site_plan
from app.models.plan import UXPlan
from app.models.requirements import ClarifiedRequirements
from app.recipes.registry import RecipeRegistry

SYSTEM = """You are a UX planner. You decide what the product's screens are, why they exist and how
a visitor moves between them.

Decide: user goals, the primary journey, information architecture, which screens are needed,
each screen's purpose, its key content, its required interactions, its route and its links.

You MUST NOT decide: CSS, spacing, colors, coordinates, component names, layout structure,
or animation. Those belong to later agents.

Keep it compact. Only screens the journey actually needs - no speculative screens. Screen ids are
lowercase snake_case and unique. Order `screens` along the journey, most important first.

Only these kinds of page can be built for this product: {page_types}. Every screen must be one of
them; a screen that fits none cannot be built, so leave it out rather than stretch a page type.

Connecting the screens:
- `route`: the screen's URL path. The entry screen is "/"; the others are short lowercase paths
  (/shop, /cart, /pricing). A screen opened for one listed thing takes an :id segment
  (/products/:id, /courses/:id) and is planned once, not once per thing.
- `nav_label`: its label in the main navigation, or null for screens that do not belong there
  (checkout, a detail page).
- `links`: the screens a visitor can reach from it, each as {{intent, to}}. The intent says what
  the visitor means to do, never which control does it; `to` is a screen id. A screen never links
  to itself. Intents:
{intents}
- `journey`: the primary path as steps {{screen, intent, to}}, in order. Every step must be one of
  that screen's links, and every screen the journey reaches has a link into it.

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

    def __init__(
        self, llm: LLMProvider, recipes: RecipeRegistry, intents: IntentRegistry | None = None
    ) -> None:
        super().__init__(llm)
        self._recipes = recipes
        self._intents = intents or default_intent_registry()

    async def plan(self, req: ClarifiedRequirements, brief: str = "") -> UXPlan:
        page_types = sorted({r.page_type for r in self._recipes.for_domain(req.domain)})
        return await self._invoke(
            SYSTEM.format(page_types=", ".join(page_types), intents=self._intents.describe()),
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

    def _validate(self, plan: UXPlan) -> UXPlan:
        # Routes the model left out are filled in; everything it wrote has to hold up.
        return validate_site_plan(normalise_routes(plan), self._intents)
