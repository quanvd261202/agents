from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.core.exceptions import UIBuilderError
from app.core.logging import get_logger
from app.graph.nodes import make_run_nodes, make_screen_nodes
from app.graph.state import AgentState, ScreenState
from app.services.container import Services

log = get_logger(__name__)


def route_after_clarifier(state: AgentState) -> str:
    out = state.get("clarifier_output")
    # needs_clarification ends the run; caller re-invokes with user_answers via checkpoint.
    return "planner" if out is not None and out.status == "ready" else END


def fan_out_screens(state: AgentState) -> list[Send]:
    """One screen pipeline per planned screen, all sharing the run's requirements and direction."""
    req, plan = state.get("clarified_requirements"), state.get("ux_plan")
    direction = state.get("design_direction")
    assert req is not None and plan is not None and direction is not None
    return [
        Send(
            "screen",
            ScreenState(
                run_id=state.get("run_id", ""),
                clarified_requirements=req,
                design_direction=direction,
                screen=screen,
                iteration=0,
            ),
        )
        for screen in plan.screens
    ]


def route_after_verifier(state: ScreenState, max_iterations: int) -> Literal["finalize", "fixer"]:
    """A screen still failing after the last fix finalizes with its open issues, never loops."""
    v = state.get("verification_result")
    if v is not None and v.status == "pass":
        return "finalize"
    return "fixer" if state.get("iteration", 0) < max_iterations else "finalize"


def route_after_fixer(state: ScreenState) -> Literal["resolver", "finalize"]:
    fix = state.get("fix_result")
    return "resolver" if fix is not None and fix.status == "success" else "finalize"


def build_screen_graph(svc: Services) -> Any:
    """build -> resolve -> render -> verify, with the fix loop, for a single screen."""
    g: StateGraph[ScreenState] = StateGraph(ScreenState)
    for name, fn in make_screen_nodes(svc).items():
        g.add_node(name, fn)  # type: ignore[call-overload]

    g.add_edge(START, "retrieval")
    g.add_edge("retrieval", "design_builder")
    g.add_edge("design_builder", "resolver")
    g.add_edge("resolver", "renderer")
    g.add_edge("renderer", "verifier")
    g.add_conditional_edges(
        "verifier",
        lambda s: route_after_verifier(s, svc.settings.max_design_iterations),
        ["fixer", "finalize"],
    )
    g.add_conditional_edges("fixer", route_after_fixer)
    g.add_edge("finalize", END)
    return g.compile()


def build_graph(svc: Services, checkpointer: Any | None = None) -> Any:
    screen_graph = build_screen_graph(svc)

    async def screen(state: ScreenState) -> dict[str, Any]:
        # One screen failing must not discard the others: record it and let the rest finish.
        try:
            return {"screens": [await screen_graph.ainvoke(state)]}
        except UIBuilderError as e:
            error = f"{type(e).__name__}: {e}"
            log.warning("screen.failed", screen=state["screen"].id, error=error)
            return {"screens": [{**state, "errors": [error]}]}

    g: StateGraph[AgentState] = StateGraph(AgentState)
    for name, fn in make_run_nodes(svc).items():
        g.add_node(name, fn)  # type: ignore[call-overload]
    g.add_node("screen", screen)

    g.add_edge(START, "clarifier")
    g.add_conditional_edges("clarifier", route_after_clarifier)
    g.add_edge("planner", "design_director")
    g.add_conditional_edges("design_director", fan_out_screens, ["screen"])
    g.add_edge("screen", END)
    return g.compile(checkpointer=checkpointer).with_config(
        max_concurrency=svc.settings.max_parallel_screens
    )
