"""M12 / Phase 17: every node is instrumented and persisted, the run is checkpointed, and the
summary says what each screen cost and whether it is accepted."""

from __future__ import annotations

import asyncio

from langgraph.checkpoint.memory import InMemorySaver

from app.agents import ClarifierAgent
from app.core.config import Settings
from app.core.llm import FakeLLMProvider
from app.core.telemetry import collect, record, totals
from app.graph.builder import build_graph
from app.graph.checkpoint import checkpointer_for, psycopg_url
from app.graph.summary import format_summary, summarize
from app.models import ClarifierOutput, RenderResult
from app.models.common import Breakpoint
from app.recipes import default_recipe_registry
from tests.conftest import REQ, StubServices, make_services

START = {"run_id": "r", "user_requirement": "shoes"}


# --- telemetry -------------------------------------------------------------------------------
def test_records_land_in_the_active_collector_only():
    record("llm", agent="x")  # no collector: dropped, never raises
    with collect() as outer:
        record("render", ms=10)
        with collect() as inner:
            record("llm", agent="fixer", input_tokens=5, output_tokens=2)
        record("retrieval", components=3)
    assert [r["kind"] for r in outer.records] == ["render", "retrieval"]
    assert inner.records == [
        {"kind": "llm", "agent": "fixer", "input_tokens": 5, "output_tokens": 2}
    ]


async def test_collectors_are_isolated_between_concurrent_tasks():
    async def work(name: str, delay: float) -> list[str]:
        with collect() as c:
            record("llm", agent=name)
            await asyncio.sleep(delay)
            record("render", ms=1)
        return [str(r.get("agent", r["kind"])) for r in c.records]

    a, b = await asyncio.gather(work("a", 0.02), work("b", 0.01))
    assert a == ["a", "render"] and b == ["b", "render"]


def test_totals_sum_calls_tokens_and_render_time():
    records = [
        {"kind": "llm", "input_tokens": 100, "output_tokens": 20},
        {"kind": "llm", "input_tokens": 50, "output_tokens": 5},
        {"kind": "render", "ms": 1200.5},
        {"kind": "retrieval", "components": 8},
        {"kind": "node", "node": "x", "ms": 3},
    ]
    assert totals(records) == {  # type: ignore[arg-type]
        "llm_calls": 2,
        "input_tokens": 150,
        "output_tokens": 25,
        "render_ms": 1200.5,
        "retrievals": 1,
    }


async def test_agents_record_every_model_call():
    llm = FakeLLMProvider([ClarifierOutput(status="ready", clarified_requirements=REQ)])
    with collect() as c:
        await ClarifierAgent(llm, default_recipe_registry()).clarify("shoes", {})
    [call] = c.records
    assert call["kind"] == "llm" and call["agent"] == "clarifier" and call["model"] == "fake"


# --- instrumented graph ----------------------------------------------------------------------
async def test_every_stage_is_persisted_in_order_and_costed(stub):
    svc = make_services(stub)
    state = await build_graph(svc).ainvoke(START)
    stages = [name for name, _ in await svc.runs.stages("r")]
    assert stages == [
        "clarifier",
        "planner",
        "design_director",
        "content_model",
        "home/retrieval",
        "home/design_builder",
        "home/copywriter",
        "home/imagery",
        "home/resolver",
        "home/renderer",
        "home/verifier",
        "home/finalize",
        "assemble",
    ]
    run_nodes = [r["node"] for r in state["usage"] if r["kind"] == "node"]
    assert run_nodes == ["clarifier", "planner", "design_director", "content_model", "assemble"]
    [screen] = state["screens"]
    screen_nodes = [r["node"] for r in screen["usage"] if r["kind"] == "node"]
    assert screen_nodes[0] == "home/retrieval" and screen_nodes[-1] == "home/finalize"
    assert all(r["ms"] >= 0 for r in screen["usage"])


async def test_persisted_stages_hold_the_outputs_without_screenshots():
    class Shots(StubServices):
        async def render(self, model, context=None):
            self.calls.append("render")
            return RenderResult(
                html="<div/>", screenshots={Breakpoint.mobile: "AAAA"}, render_time_ms=12.0
            )

    svc = make_services(Shots())
    await build_graph(svc).ainvoke(START)
    by_stage = dict(await svc.runs.stages("r"))
    assert by_stage["clarifier"]["clarified_requirements"]["domain"] == "ecommerce"
    assert by_stage["home/design_builder"]["design_spec"]["screen_id"] == "home"
    render = by_stage["home/renderer"]["render_result"]
    assert render["render_time_ms"] == 12.0
    assert "screenshots" not in render and "html" not in render
    assert by_stage["home/verifier"]["verification_result"]["status"] == "pass"
    assert by_stage["home/finalize"] == {}


async def test_fixes_are_persisted_with_their_iteration():
    svc = make_services(StubServices(fail_times=1))
    await build_graph(svc).ainvoke(START)
    stages = await svc.runs.stages("r")
    fixes = [p for name, p in stages if name == "home/fixer"]
    assert len(fixes) == 1 and fixes[0]["iteration"] == 1
    assert fixes[0]["fix_result"]["status"] == "success"
    assert [n for n, _ in stages].count("home/verifier") == 2


# --- checkpointing ---------------------------------------------------------------------------
async def test_clarification_round_trip_sends_only_the_answers_on_the_second_pass():
    stub = StubServices(ready=False)
    graph = build_graph(make_services(stub), InMemorySaver())
    config = {"configurable": {"thread_id": "r"}}
    first = await graph.ainvoke(START, config)
    assert first["clarifier_output"].status == "needs_clarification"
    assert not first.get("screens")

    stub.ready = True
    second = await graph.ainvoke({"user_answers": {"Who?": "runners"}}, config)
    assert second["user_requirement"] == "shoes"  # restored from the checkpoint
    assert second["user_answers"] == {"Who?": "runners"}
    assert [s["screen"].id for s in second["screens"]] == ["home"]
    assert stub.calls.count("clarify") == 2 and stub.calls.count("plan") == 1


async def test_memory_checkpointer_when_persistence_is_memory():
    async with checkpointer_for(Settings(persistence="memory", _env_file=None)) as saver:
        assert isinstance(saver, InMemorySaver)


async def test_unreachable_postgres_falls_back_to_memory_checkpoints():
    settings = Settings(
        persistence="postgres",
        database_url="postgresql+asyncpg://u:p@127.0.0.1:1/uib",
        _env_file=None,
    )
    async with checkpointer_for(settings) as saver:
        assert isinstance(saver, InMemorySaver)


def test_psycopg_url_swaps_the_driver():
    assert psycopg_url("postgresql+asyncpg://u:p@h:5432/d") == "postgresql://u:p@h:5432/d"


# --- summary ---------------------------------------------------------------------------------
async def test_summary_reports_cost_fixes_and_acceptance():
    stub = StubServices(fail_times=1, screens=("home", "detail"))
    state = await build_graph(make_services(stub)).ainvoke(START)
    summary = summarize(state)
    assert summary["run_id"] == "r" and summary["accepted"] is True
    by_id = {s["screen"]: s for s in summary["screens"]}
    assert sorted(s["fixes"] for s in by_id.values()) == [0, 1]
    fixed = next(s for s in by_id.values() if s["fixes"] == 1)
    assert fixed["status"] == "pass" and fixed["fix_source"] == "model"
    assert fixed["issues"] == {"critical": 0, "major": 0, "minor": 0}
    assert summary["llm_calls"] == 0  # stubs make no model calls
    text = format_summary(summary)
    assert "run         accepted" in text and "home" in text and "detail" in text


async def test_a_screen_out_of_fix_budget_is_not_accepted():
    stub = StubServices(fail_times=10)
    state = await build_graph(make_services(stub, max_iter=1)).ainvoke(START)
    summary = summarize(state)
    [screen] = summary["screens"]
    assert screen["status"] == "needs_fix" and screen["accepted"] is False
    assert screen["issues"]["major"] == 1
    assert summary["accepted"] is False
    assert "not accepted" in format_summary(summary)


async def test_a_failed_screen_is_reported_not_accepted():
    from app.core.exceptions import ValidationError

    class Breaks(StubServices):
        async def build(self, req, screen, direction, ctx):
            raise ValidationError("boom")

    state = await build_graph(make_services(Breaks())).ainvoke(START)
    [screen] = summarize(state)["screens"]
    assert screen["status"] == "failed" and screen["errors"] == ["ValidationError: boom"]
    assert screen["accepted"] is False
