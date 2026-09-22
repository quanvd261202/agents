from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import make_nodes
from app.graph.state import AgentState
from app.services.container import Services


def route_after_clarifier(state: AgentState) -> str:
    out = state.get("clarifier_output")
    # needs_clarification ends the run; caller re-invokes with user_answers via checkpoint.
    return "planner" if out is not None and out.status == "ready" else END


def route_after_verifier(state: AgentState) -> Literal["finalize", "fixer"]:
    v = state.get("verification_result")
    return "finalize" if v is not None and v.status == "pass" else "fixer"


def route_after_fixer(state: AgentState) -> Literal["resolver", "finalize"]:
    fix = state.get("fix_result")
    return "resolver" if fix is not None and fix.status == "success" else "finalize"


def build_graph(svc: Services, checkpointer: Any | None = None) -> Any:
    nodes = make_nodes(svc)
    g: StateGraph[AgentState] = StateGraph(AgentState)
    for name, fn in nodes.items():
        g.add_node(name, fn)  # type: ignore[call-overload]

    g.add_edge(START, "clarifier")
    g.add_conditional_edges("clarifier", route_after_clarifier)
    g.add_edge("planner", "design_director")
    g.add_edge("design_director", "retrieval")
    g.add_edge("retrieval", "design_builder")
    g.add_edge("design_builder", "resolver")
    g.add_edge("resolver", "renderer")
    g.add_edge("renderer", "verifier")
    g.add_conditional_edges("verifier", route_after_verifier)
    g.add_conditional_edges("fixer", route_after_fixer)
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)
