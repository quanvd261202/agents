"""Thin LangGraph nodes. Business logic lives in services; nodes only marshal state."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.core.exceptions import UIBuilderError
from app.core.logging import get_logger
from app.graph.state import AgentState, ScreenState
from app.models import DesignDirection, DesignSpec, ScreenPlan
from app.services.container import Services

log = get_logger(__name__)
Node = Callable[[Any], Awaitable[dict[str, Any]]]


def _require(state: AgentState | ScreenState, key: str) -> Any:
    value = state.get(key)
    if value is None:
        raise UIBuilderError(f"state['{key}'] is required at this stage")
    return value


def make_run_nodes(svc: Services) -> dict[str, Node]:
    """Run-level stages: they decide once for the whole product."""

    async def clarifier(state: AgentState) -> dict[str, Any]:
        out = await svc.clarifier.clarify(state["user_requirement"], state.get("user_answers", {}))
        return {"clarifier_output": out, "clarified_requirements": out.clarified_requirements}

    async def planner(state: AgentState) -> dict[str, Any]:
        # The user's own words go downstream verbatim: the clarified summary is lossy.
        plan = await svc.planner.plan(
            _require(state, "clarified_requirements"), state.get("user_requirement", "")
        )
        return {"ux_plan": plan}

    async def design_director(state: AgentState) -> dict[str, Any]:
        d = await svc.director.direct(
            _require(state, "clarified_requirements"),
            _require(state, "ux_plan"),
            state.get("user_requirement", ""),
        )
        return {"design_direction": d}

    return {"clarifier": clarifier, "planner": planner, "design_director": design_director}


def make_screen_nodes(svc: Services) -> dict[str, Node]:
    """Per-screen stages: each planned screen runs through these on its own."""

    async def retrieval(state: ScreenState) -> dict[str, Any]:
        direction: DesignDirection = _require(state, "design_direction")
        screen: ScreenPlan = _require(state, "screen")
        ctx = await svc.retrieval.retrieve(
            _require(state, "clarified_requirements"), direction, direction.recipe_for(screen.id)
        )
        log.info(
            "retrieval.context",
            screen=screen.id,
            components=len(ctx.components),
            layouts=len(ctx.layouts),
            tokens=ctx.estimated_tokens,
        )
        return {"retrieved_context": ctx}

    async def design_builder(state: ScreenState) -> dict[str, Any]:
        ctx = _require(state, "retrieved_context")
        spec = await svc.builder.build(
            _require(state, "clarified_requirements"),
            _require(state, "screen"),
            _require(state, "design_direction"),
            ctx,
        )
        return {"design_spec": spec, "iteration": 0}

    async def resolver(state: ScreenState) -> dict[str, Any]:
        return {"resolved_design": svc.resolver.resolve(_require(state, "design_spec"))}

    async def renderer(state: ScreenState) -> dict[str, Any]:
        return {"render_result": await svc.renderer.render(_require(state, "resolved_design"))}

    async def verifier(state: ScreenState) -> dict[str, Any]:
        v = await svc.verifier.verify(
            _require(state, "design_spec"),
            _require(state, "resolved_design"),
            _require(state, "render_result"),
        )
        return {"verification_result": v}

    async def fixer(state: ScreenState) -> dict[str, Any]:
        iteration = state.get("iteration", 0) + 1
        spec: DesignSpec = _require(state, "design_spec")
        fix = await svc.fixer.fix(spec, _require(state, "verification_result"))
        new_spec = svc.fixer.apply(spec, fix) if fix.status == "success" else spec
        return {"fix_result": fix, "design_spec": new_spec, "iteration": iteration}

    async def finalize(state: ScreenState) -> dict[str, Any]:
        log.info(
            "screen.finalized",
            run_id=state.get("run_id"),
            screen=_require(state, "screen").id,
            iteration=state.get("iteration", 0),
        )
        return {}

    return {
        "retrieval": retrieval,
        "design_builder": design_builder,
        "resolver": resolver,
        "renderer": renderer,
        "verifier": verifier,
        "fixer": fixer,
        "finalize": finalize,
    }
