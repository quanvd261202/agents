"""Thin LangGraph nodes. Business logic lives in services; nodes only marshal state."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel

from app.core.exceptions import UIBuilderError
from app.core.logging import get_logger
from app.core.telemetry import collect
from app.graph.state import AgentState, ScreenState
from app.models import DesignDirection, DesignSpec, ScreenPlan
from app.services.container import Services
from app.services.repositories import RunRepository

log = get_logger(__name__)
Node = Callable[[Any], Awaitable[dict[str, Any]]]

#: Persisted stages hold the render's findings and timing, never its screenshots or HTML.
_STAGE_EXCLUDES: dict[str, set[str]] = {"render_result": {"screenshots", "html", "dom_outline"}}


def _require(state: AgentState | ScreenState, key: str) -> Any:
    value = state.get(key)
    if value is None:
        raise UIBuilderError(f"state['{key}'] is required at this stage")
    return value


def _payload(out: dict[str, Any]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in out.items():
        if key == "usage":
            continue
        if isinstance(value, BaseModel):
            payload[key] = value.model_dump(mode="json", exclude=_STAGE_EXCLUDES.get(key))
        elif isinstance(value, list) and value and isinstance(value[0], BaseModel):
            payload[key] = [v.model_dump(mode="json") for v in value]
        else:
            payload[key] = value
    return payload


def instrument(name: str, fn: Node, runs: RunRepository) -> Node:
    """Phase 17 around every node: what it cost (model calls, retrievals, renders, its own time)
    goes into `usage`, and what it produced is persisted as a stage of the run."""

    async def node(state: AgentState | ScreenState) -> dict[str, Any]:
        start = time.perf_counter()
        with collect() as collector:
            out = await fn(state)
        ms = round((time.perf_counter() - start) * 1000, 1)
        screen = state.get("screen")
        stage = f"{screen.id}/{name}" if isinstance(screen, ScreenPlan) else name
        try:
            await runs.save_stage(state.get("run_id", ""), stage, _payload(out))
        except Exception as e:  # noqa: BLE001 - persistence never fails a run
            log.warning("persistence.stage_failed", stage=stage, error=str(e))
        return {**out, "usage": [*collector.records, {"kind": "node", "node": stage, "ms": ms}]}

    return node


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

    nodes = {"clarifier": clarifier, "planner": planner, "design_director": design_director}
    return {name: instrument(name, fn, svc.runs) for name, fn in nodes.items()}


def make_screen_nodes(svc: Services) -> dict[str, Node]:
    """Per-screen stages: each planned screen runs through these on its own."""

    async def retrieval(state: ScreenState) -> dict[str, Any]:
        direction: DesignDirection = _require(state, "design_direction")
        screen: ScreenPlan = _require(state, "screen")
        req = _require(state, "clarified_requirements")
        recipe = direction.recipe_for(screen.id)
        # Confirmed lessons about this kind of page reach the Builder with the catalog context.
        lessons = await svc.learning.advise(req, direction, recipe)
        ctx = await svc.retrieval.retrieve(req, direction, recipe, lessons)
        log.info(
            "retrieval.context",
            screen=screen.id,
            components=len(ctx.components),
            layouts=len(ctx.layouts),
            lessons=len(ctx.lessons),
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

    async def copywriter(state: ScreenState) -> dict[str, Any]:
        spec = await svc.copywriter.write(
            _require(state, "clarified_requirements"),
            _require(state, "screen"),
            _require(state, "design_direction"),
            _require(state, "design_spec"),
            state.get("user_requirement", ""),
        )
        return {"design_spec": spec}

    async def imagery(state: ScreenState) -> dict[str, Any]:
        return {"design_spec": await svc.imagery.illustrate(_require(state, "design_spec"))}

    async def resolver(state: ScreenState) -> dict[str, Any]:
        return {"resolved_design": svc.resolver.resolve(_require(state, "design_spec"))}

    async def renderer(state: ScreenState) -> dict[str, Any]:
        return {"render_result": await svc.renderer.render(_require(state, "resolved_design"))}

    async def verifier(state: ScreenState) -> dict[str, Any]:
        spec: DesignSpec = _require(state, "design_spec")
        v = await svc.verifier.verify(
            spec, _require(state, "resolved_design"), _require(state, "render_result")
        )
        # After a fix, the verification before it is still in state: what disappeared between
        # the two is what the fix taught us.
        before, fix = state.get("verification_result"), state.get("fix_result")
        events: list[Any] = []
        if before is not None and fix is not None and state.get("iteration", 0) > 0:
            events = await svc.learning.learn(
                before,
                fix,
                v,
                spec,
                _require(state, "clarified_requirements").domain,
                state.get("run_id", ""),
            )
        return {"verification_result": v, "learning_events": events}

    async def fixer(state: ScreenState) -> dict[str, Any]:
        iteration = state.get("iteration", 0) + 1
        spec: DesignSpec = _require(state, "design_spec")
        verification = _require(state, "verification_result")
        lessons = await svc.learning.suggest(
            spec, verification, _require(state, "clarified_requirements").domain
        )
        fix = await svc.fixer.fix(spec, verification, lessons)
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

    nodes = {
        "retrieval": retrieval,
        "design_builder": design_builder,
        "copywriter": copywriter,
        "imagery": imagery,
        "resolver": resolver,
        "renderer": renderer,
        "verifier": verifier,
        "fixer": fixer,
        "finalize": finalize,
    }
    return {name: instrument(name, fn, svc.runs) for name, fn in nodes.items()}
