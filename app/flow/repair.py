"""Site plan repair: patches are proposed (by rules here, or by the flow fixer agent), applied to
a copy of the plan, and kept only if the patched plan validates. The plan in state is never
mutated in place."""

from __future__ import annotations

from app.catalog.registry import ComponentRegistry
from app.core.exceptions import ValidationError
from app.flow.intents import IntentRegistry
from app.flow.siteplan import validate_intent_targets, validate_site_plan
from app.models.direction import DesignDirection
from app.models.flow import FlowReport, SitePlanPatch
from app.models.plan import Link, UXPlan
from app.recipes.registry import RecipeRegistry


def apply_patches(
    plan: UXPlan,
    patches: list[SitePlanPatch],
    intents: IntentRegistry,
    direction: DesignDirection | None = None,
    recipes: RecipeRegistry | None = None,
) -> UXPlan:
    """The plan with every patch applied, validated as the planner's output is. Raises
    ValidationError (naming the patch) when a patch cannot apply or the result does not hold."""
    screens = {s.id: s for s in plan.screens}
    for i, p in enumerate(patches, 1):
        s = screens.get(p.screen)
        if s is None:
            raise ValidationError(f"patch {i}: no screen '{p.screen}'", target=p.screen)
        if p.op == "set_route":
            if not p.route:
                raise ValidationError(f"patch {i}: set_route needs a route", target=p.screen)
            screens[p.screen] = s.model_copy(update={"route": p.route})
            continue
        if not p.intent or not p.to:
            raise ValidationError(f"patch {i}: {p.op} needs intent and to", target=p.screen)
        if p.op == "add_edge":
            links = [*s.links, Link(intent=p.intent, to=p.to)]
        else:  # retarget_edge
            if not any(link.intent == p.intent for link in s.links):
                raise ValidationError(
                    f"patch {i}: '{p.screen}' has no {p.intent} link to retarget", target=p.screen
                )
            links = [
                link.model_copy(update={"to": p.to}) if link.intent == p.intent else link
                for link in s.links
            ]
        screens[p.screen] = s.model_copy(update={"links": links})
    patched = plan.model_copy(update={"screens": [screens[s.id] for s in plan.screens]})
    validate_site_plan(patched, intents)
    if direction is not None and recipes is not None:
        validate_intent_targets(patched, direction, recipes, intents)
    return patched


def rule_patches(
    plan: UXPlan,
    report: FlowReport,
    direction: DesignDirection,
    recipes: RecipeRegistry,
    components: ComponentRegistry,
    intents: IntentRegistry,
) -> list[SitePlanPatch]:
    """Deterministic repairs. A dead control emits intents its screen never links; when the plan
    has a screen of the kind one of those intents means, the missing edge is added. A failed
    journey step whose link is absent gets the link. Anything else is left to the model."""
    by_id = {s.id: s for s in plan.screens}
    page_type = {s.id: recipes.get(direction.recipe_for(s.id)).page_type for s in plan.screens}
    patches: list[SitePlanPatch] = []
    seen: set[tuple[str, str, str]] = set()

    def add(screen: str, intent: str, to: str) -> None:
        if (screen, intent, to) in seen or to == screen:
            return
        if any(link.intent == intent for link in by_id[screen].links):
            return
        seen.add((screen, intent, to))
        patches.append(SitePlanPatch(op="add_edge", screen=screen, intent=intent, to=to))

    for step in report.failed_steps():
        if step.screen in by_id and step.to in by_id:
            add(step.screen, step.intent, step.to)

    for dead in report.dead:
        if dead.screen not in by_id:
            continue
        comp = next((c for c in components if c.id == dead.section), None)
        candidates = comp.emits.get(dead.role, []) if comp is not None else []
        for intent_id in candidates:
            if not intents.exists(intent_id):
                continue
            intent = intents.get(intent_id)
            if intent.home:
                continue  # go_home is implicit everywhere
            if not intent.page_types:
                continue  # an open-ended intent has no obvious target: the model decides
            if page_type[dead.screen] in intent.page_types:
                continue  # already on that kind of page: "browse" on the listing goes nowhere
            target = next(
                (
                    s.id
                    for s in plan.screens
                    if s.id != dead.screen and page_type[s.id] in intent.page_types
                ),
                None,
            )
            if target is not None:
                add(dead.screen, intent_id, target)
                break
    return patches
