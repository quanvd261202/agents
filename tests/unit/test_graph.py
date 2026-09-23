import asyncio

from app.core.exceptions import ValidationError
from app.graph.builder import build_graph
from app.models import ScreenDirection
from tests.conftest import StubServices, make_services

START = {"run_id": "r", "user_requirement": "shoes"}


async def test_happy_path_runs_all_stages_once(stub):
    graph = build_graph(make_services(stub))
    state = await graph.ainvoke(START)
    [screen] = state["screens"]
    assert screen["verification_result"].status == "pass"
    assert screen["iteration"] == 0
    assert stub.calls.count("render") == 1


async def test_needs_clarification_stops_before_planner():
    stub = StubServices(ready=False)
    graph = build_graph(make_services(stub))
    state = await graph.ainvoke(START)
    assert state["clarifier_output"].status == "needs_clarification"
    assert "plan" not in stub.calls
    assert not state.get("screens")


async def test_fix_loop_rerenders_then_passes():
    stub = StubServices(fail_times=2)
    graph = build_graph(make_services(stub))
    state = await graph.ainvoke(START)
    [screen] = state["screens"]
    assert screen["iteration"] == 2
    assert stub.calls.count("render") == 3
    assert screen["verification_result"].status == "pass"


async def test_iteration_limit_finalizes_with_the_open_issues():
    stub = StubServices(fail_times=10)
    graph = build_graph(make_services(stub, max_iter=2))
    state = await graph.ainvoke(START)
    [screen] = state["screens"]
    assert screen["iteration"] == 2
    assert screen["verification_result"].status == "needs_fix"
    assert not screen.get("errors")
    assert stub.calls.count("render") == 3  # the first render plus two fixes, then it stops
    assert stub.calls.count("fix") == 2


async def test_fixer_failure_finalizes_without_rerender():
    stub = StubServices(fail_times=1, fixer_ok=False)
    graph = build_graph(make_services(stub))
    state = await graph.ainvoke(START)
    [screen] = state["screens"]
    assert screen["fix_result"].status == "failure"
    assert stub.calls.count("render") == 1


# --- every planned screen --------------------------------------------------------------------
SCREENS = ("home", "listing", "detail", "cart", "checkout")


async def test_every_planned_screen_is_built_in_plan_order():
    stub = StubServices(screens=SCREENS)
    state = await build_graph(make_services(stub)).ainvoke(START)
    assert [s["screen"].id for s in state["screens"]] == list(SCREENS)
    assert [s["design_spec"].screen_id for s in state["screens"]] == list(SCREENS)
    assert stub.calls.count("build") == stub.calls.count("render") == len(SCREENS)
    # run-level decisions are made once, not per screen
    assert stub.calls.count("plan") == stub.calls.count("direct") == 1


async def test_screen_order_does_not_depend_on_which_finishes_first():
    class SlowFirst(StubServices):
        async def build(self, req, screen, direction, ctx):
            # the first screen finishes last
            await asyncio.sleep(0.05 * (len(SCREENS) - SCREENS.index(screen.id)))
            return await super().build(req, screen, direction, ctx)

    state = await build_graph(make_services(SlowFirst(screens=SCREENS))).ainvoke(START)
    assert [s["screen"].id for s in state["screens"]] == list(SCREENS)


async def test_each_screen_is_retrieved_with_its_own_recipe():
    recipes = {"home": "saas_landing", "overview": "dashboard"}
    seen: list[str] = []

    class PerScreen(StubServices):
        async def direct(self, req, plan, brief=""):
            d = await super().direct(req, plan, brief)
            return d.model_copy(
                update={
                    "screens": [ScreenDirection(screen_id=k, recipe=v) for k, v in recipes.items()]
                }
            )

        async def retrieve(self, req, direction, recipe, lessons=None):
            seen.append(recipe)
            return await super().retrieve(req, direction, recipe, lessons)

    await build_graph(make_services(PerScreen(screens=tuple(recipes)))).ainvoke(START)
    assert sorted(seen) == ["dashboard", "saas_landing"]


async def test_a_failing_screen_does_not_discard_the_others():
    class CartBreaks(StubServices):
        async def build(self, req, screen, direction, ctx):
            if screen.id == "cart":
                raise ValidationError("section 'x' is not part of recipe y")
            return await super().build(req, screen, direction, ctx)

    state = await build_graph(make_services(CartBreaks(screens=SCREENS))).ainvoke(START)
    by_id = {s["screen"].id: s for s in state["screens"]}
    assert list(by_id) == list(SCREENS)
    assert by_id["cart"]["errors"] == ["ValidationError: section 'x' is not part of recipe y"]
    assert "design_spec" not in by_id["cart"]
    assert all(by_id[s]["verification_result"].status == "pass" for s in SCREENS if s != "cart")


async def test_fix_loops_are_independent_per_screen():
    stub = StubServices(fail_times=1, screens=("home", "detail"))
    state = await build_graph(make_services(stub)).ainvoke(START)
    # one screen needed a fix, the other passed first time; both end passing
    assert sorted(s["iteration"] for s in state["screens"]) == [0, 1]
    assert all(s["verification_result"].status == "pass" for s in state["screens"])
    assert stub.calls.count("render") == 3


async def test_the_users_brief_reaches_the_planner_verbatim(stub):
    await build_graph(make_services(stub)).ainvoke(START)
    assert stub.briefs == [START["user_requirement"]]
