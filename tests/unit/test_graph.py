import pytest

from app.core.exceptions import IterationLimitExceeded
from app.graph.builder import build_graph
from tests.conftest import StubServices, make_services

START = {"run_id": "r", "user_requirement": "shoes", "iteration": 0}


async def test_happy_path_runs_all_stages_once(stub):
    graph = build_graph(make_services(stub))
    state = await graph.ainvoke(START)
    assert state["verification_result"].status == "pass"
    assert state["iteration"] == 0
    assert stub.calls.count("render") == 1


async def test_needs_clarification_stops_before_planner():
    stub = StubServices(ready=False)
    graph = build_graph(make_services(stub))
    state = await graph.ainvoke(START)
    assert state["clarifier_output"].status == "needs_clarification"
    assert "plan" not in stub.calls


async def test_fix_loop_rerenders_then_passes():
    stub = StubServices(fail_times=2)
    graph = build_graph(make_services(stub))
    state = await graph.ainvoke(START)
    assert state["iteration"] == 2
    assert stub.calls.count("render") == 3
    assert state["verification_result"].status == "pass"


async def test_iteration_limit_is_enforced():
    stub = StubServices(fail_times=10)
    graph = build_graph(make_services(stub, max_iter=2))
    with pytest.raises(IterationLimitExceeded):
        await graph.ainvoke(START)


async def test_fixer_failure_finalizes_without_rerender():
    stub = StubServices(fail_times=1, fixer_ok=False)
    graph = build_graph(make_services(stub))
    state = await graph.ainvoke(START)
    assert state["fix_result"].status == "failure"
    assert stub.calls.count("render") == 1
