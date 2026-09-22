"""Thin LangGraph nodes. Business logic lives in services; nodes only marshal state."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.core.exceptions import IterationLimitExceeded, UIBuilderError
from app.core.logging import get_logger
from app.graph.state import AgentState
from app.models import DesignSpec
from app.services.container import Services

log = get_logger(__name__)
Node = Callable[[AgentState], Awaitable[dict[str, Any]]]


def _require(state: AgentState, key: str) -> Any:
    value = state.get(key)
    if value is None:
        raise UIBuilderError(f"state['{key}'] is required at this stage")
    return value


def make_nodes(svc: Services) -> dict[str, Node]:
    async def clarifier(state: AgentState) -> dict[str, Any]:
        out = await svc.clarifier.clarify(state["user_requirement"], state.get("user_answers", {}))
        return {"clarifier_output": out, "clarified_requirements": out.clarified_requirements}

    async def planner(state: AgentState) -> dict[str, Any]:
        return {"ux_plan": await svc.planner.plan(_require(state, "clarified_requirements"))}

    async def design_director(state: AgentState) -> dict[str, Any]:
        d = await svc.director.direct(
            _require(state, "clarified_requirements"), _require(state, "ux_plan")
        )
        return {"design_direction": d}

    async def retrieval(state: AgentState) -> dict[str, Any]:
        ctx = await svc.retrieval.retrieve(
            _require(state, "clarified_requirements"), _require(state, "design_direction")
        )
        log.info(
            "retrieval.context",
            components=len(ctx.components),
            layouts=len(ctx.layouts),
            tokens=ctx.estimated_tokens,
        )
        return {"retrieved_context": ctx}

    async def design_builder(state: AgentState) -> dict[str, Any]:
        ctx = _require(state, "retrieved_context")
        spec = await svc.builder.build(
            _require(state, "clarified_requirements"),
            _require(state, "ux_plan"),
            _require(state, "design_direction"),
            ctx,
        )
        return {"design_spec": spec, "iteration": 0}

    async def resolver(state: AgentState) -> dict[str, Any]:
        return {"resolved_design": svc.resolver.resolve(_require(state, "design_spec"))}

    async def renderer(state: AgentState) -> dict[str, Any]:
        return {"render_result": await svc.renderer.render(_require(state, "resolved_design"))}

    async def verifier(state: AgentState) -> dict[str, Any]:
        v = await svc.verifier.verify(
            _require(state, "design_spec"),
            _require(state, "resolved_design"),
            _require(state, "render_result"),
        )
        return {"verification_result": v}

    async def fixer(state: AgentState) -> dict[str, Any]:
        iteration = state.get("iteration", 0) + 1
        if iteration > svc.settings.max_design_iterations:
            raise IterationLimitExceeded(
                f"exceeded {svc.settings.max_design_iterations} design iterations"
            )
        spec: DesignSpec = _require(state, "design_spec")
        fix = await svc.fixer.fix(spec, _require(state, "verification_result"))
        new_spec = svc.fixer.apply(spec, fix) if fix.status == "success" else spec
        return {"fix_result": fix, "design_spec": new_spec, "iteration": iteration}

    async def finalize(state: AgentState) -> dict[str, Any]:
        log.info("run.finalized", run_id=state.get("run_id"), iteration=state.get("iteration", 0))
        return {}

    return {
        "clarifier": clarifier,
        "planner": planner,
        "design_director": design_director,
        "retrieval": retrieval,
        "design_builder": design_builder,
        "resolver": resolver,
        "renderer": renderer,
        "verifier": verifier,
        "fixer": fixer,
        "finalize": finalize,
    }
