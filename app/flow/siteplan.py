"""Site plan validation: routes, links and journeys on the UX plan. Screen id is the identity;
the route is a property of the screen."""

from __future__ import annotations

import re

from app.core.exceptions import ValidationError
from app.flow.intents import IntentRegistry
from app.models.direction import DesignDirection
from app.models.plan import UXPlan
from app.models.site import default_route
from app.recipes.registry import RecipeRegistry

_ROUTE = re.compile(r"^/(?:[a-z0-9-]+|:[a-z_]+)(?:/(?:[a-z0-9-]+|:[a-z_]+))*$")


def normalise_routes(plan: UXPlan) -> UXPlan:
    """Fill the routes the planner left out from the screen ids; the first screen is the entry
    unless the planner put another screen at `/`. Nothing the planner did write is changed."""
    has_entry = any(s.route == "/" for s in plan.screens)
    screens = [
        s
        if s.route is not None
        else s.model_copy(update={"route": default_route(s.id, i == 0 and not has_entry)})
        for i, s in enumerate(plan.screens)
    ]
    return plan.model_copy(update={"screens": screens})


def route_params(route: str) -> list[str]:
    return [seg[1:] for seg in route.split("/") if seg.startswith(":")]


def validate_site_plan(plan: UXPlan, intents: IntentRegistry) -> UXPlan:
    """Every route well-formed and unique with one entry at `/`, every link an intent from the
    vocabulary to another planned screen, and every journey step one of its screen's links."""
    ids = [s.id for s in plan.screens]
    if len(ids) != len(set(ids)):
        raise ValidationError(f"duplicate screen ids: {ids}", target="screens")
    by_id = {s.id: s for s in plan.screens}

    routes: dict[str, str] = {}
    for s in plan.screens:
        if s.route is None:
            raise ValidationError(f"screen '{s.id}' has no route", target=s.id)
        if s.route != "/" and not _ROUTE.match(s.route):
            raise ValidationError(
                f"route '{s.route}' of '{s.id}' is not a lowercase path like /shop, /cart or "
                "/products/:id",
                target=s.id,
            )
        if s.route in routes:
            raise ValidationError(
                f"route '{s.route}' is used by both '{routes[s.route]}' and '{s.id}'", target=s.id
            )
        routes[s.route] = s.id
    if "/" not in routes:
        raise ValidationError("one screen must have the route '/'", target="screens")

    for s in plan.screens:
        seen: set[tuple[str, str]] = set()
        for link in s.links:
            if not intents.exists(link.intent):
                raise ValidationError(
                    f"'{s.id}' links with unknown intent '{link.intent}'; "
                    f"use one of {intents.ids()}",
                    target=s.id,
                )
            if link.to not in by_id:
                raise ValidationError(
                    f"'{s.id}' links to '{link.to}', which is not a planned screen", target=s.id
                )
            if link.to == s.id:
                raise ValidationError(f"'{s.id}' links to itself", target=s.id)
            if (link.intent, link.to) in seen:
                raise ValidationError(
                    f"'{s.id}' repeats the link {link.intent} -> {link.to}", target=s.id
                )
            seen.add((link.intent, link.to))
            intent = intents.get(link.intent)
            target = by_id[link.to]
            if intent.per_item and len(route_params(target.route or "")) != 1:
                raise ValidationError(
                    f"'{target.id}' is opened per item ({link.intent} from '{s.id}'), so its "
                    f"route needs one :id segment, e.g. /products/:id; got '{target.route}'",
                    target=target.id,
                )
            if intent.home and target.route != "/":
                raise ValidationError(
                    f"'{s.id}' uses {link.intent} to reach '{target.id}', but the entry screen "
                    f"(route '/') is '{routes['/']}'",
                    target=s.id,
                )

    for i, step in enumerate(plan.journey, 1):
        for sid in (step.screen, step.to):
            if sid not in by_id:
                raise ValidationError(
                    f"journey step {i} names '{sid}', which is not a planned screen",
                    target="journey",
                )
        if not any(
            link.intent == step.intent and link.to == step.to for link in by_id[step.screen].links
        ):
            raise ValidationError(
                f"journey step {i} ({step.screen} --{step.intent}--> {step.to}) is not one of "
                f"'{step.screen}'s links; add the link or change the step",
                target="journey",
            )
    return plan


def validate_intent_targets(
    plan: UXPlan, direction: DesignDirection, recipes: RecipeRegistry, intents: IntentRegistry
) -> None:
    """Once recipes are assigned, a link's target has to be the kind of page its intent means:
    `view_cart` cannot land on a storefront. Raised for the Director, which chooses recipes."""
    for s in plan.screens:
        for link in s.links:
            intent = intents.get(link.intent)
            if not intent.page_types:
                continue
            recipe = recipes.get(direction.recipe_for(link.to))
            if recipe.page_type not in intent.page_types:
                raise ValidationError(
                    f"'{link.to}' is reached by {link.intent} from '{s.id}', so it needs a "
                    f"{' or '.join(intent.page_types)} recipe, not '{recipe.id}' "
                    f"({recipe.page_type})",
                    target=link.to,
                )
