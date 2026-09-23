"""M11 / Phase 16 learning: lessons mined from verified fixes, promoted by repetition, handed
back to the Builder as advice and to the Fixer as hints or, once trusted, as a deterministic fix."""

from __future__ import annotations

import pytest

from app.agents import FixerAgent
from app.agents.fixer import FixerOutput
from app.catalog import default_component_registry
from app.core.llm import FakeLLMProvider
from app.dsl import default_design_resolver
from app.graph.builder import build_graph
from app.learning import (
    InMemoryLessonRepository,
    LearningService,
    describe,
    lesson_id,
    signature,
    status_for,
)
from app.models import (
    ClarifiedRequirements,
    DesignDirection,
    DesignSpec,
    FixResult,
    Issue,
    Lesson,
    Patch,
    ScreenDirection,
    VerificationResult,
)
from app.recipes import default_recipe_registry
from app.retrieval import HashingEmbeddingProvider
from tests.conftest import StubServices, make_services

REQ = ClarifiedRequirements(
    product="Ember & Leaf",
    domain="ecommerce",
    target_audience="home baristas",
    primary_goal="sell coffee",
)
DIRECTION = DesignDirection(
    visual_style="warm_editorial",
    theme="premium_light",
    typography="editorial_serif",
    radius="large",
    layout_strategy="editorial_grid",
    animation="subtle",
    screens=[ScreenDirection(screen_id="home", recipe="ecommerce_home")],
)
SPEC = DesignSpec(
    screen_id="home",
    recipe="ecommerce_home",
    visual_style="warm_editorial",
    theme="premium_light",
    sections=[
        {"id": "navigation", "type": "navigation"},
        {"id": "hero", "type": "hero", "content": {"headline": "Ember Roast, back for autumn"}},
        {
            "id": "featured_products",
            "type": "product_grid",
            "variant": "premium",
            "content": {"title": "Ember Roast and friends"},
        },
        {"id": "footer", "type": "footer"},
    ],
)
NARROW = Issue(
    severity="critical",
    dimension="layout",
    target="featured_products",
    issue="[desktop] grid columns are 180px wide, too narrow for their content",
    suggestion="fewer columns",
    deterministic=True,
)
CLUTTER = Issue(
    severity="major",
    dimension="visual",
    target="hero",
    issue="The hero headline 'Ember Roast, back for autumn' fights the badge",
    suggestion="calmer variant",
)
COLUMNS_3 = FixResult(
    status="success", patches=[Patch(target="featured_products", property="columns", value="3")]
)
FAILING = VerificationResult(status="needs_fix", issues=[NARROW])
PASSING = VerificationResult(status="pass")
SCOPE = {
    "domain": "ecommerce",
    "page_type": "storefront",
    "component": "product_grid",
    "problem": "grid columns are Npx wide, too narrow for their content",
}
FIX = {"property": "columns", "value": "3"}


def service() -> LearningService:
    return LearningService(
        InMemoryLessonRepository(HashingEmbeddingProvider(64)), default_recipe_registry()
    )


async def lesson(svc: LearningService, times: int, *, failures: int = 0) -> Lesson:
    for _ in range(times):
        await svc.learn(FAILING, COLUMNS_3, PASSING, SPEC, "ecommerce", "run-1")
    for _ in range(failures):
        await svc.learn(FAILING, COLUMNS_3, FAILING, SPEC, "ecommerce", "run-2")
    found = await svc._repository.get(lesson_id(SCOPE, FIX))
    assert found is not None
    return found


# --- pure pieces -----------------------------------------------------------------------------
def test_signature_drops_what_varies_between_screens():
    assert signature(NARROW) == "grid columns are Npx wide, too narrow for their content"
    assert signature(CLUTTER) == "visual issue"  # model wording is never a key


def test_status_needs_repeated_confirmation_and_demotes_on_violations():
    assert status_for(1, 0) == "candidate"
    assert status_for(2, 0) == "validated"
    assert status_for(3, 0) == "trusted"
    assert status_for(4, 2) == "candidate"  # violations rival confirmations
    assert status_for(6, 1) == "trusted"


def test_lesson_id_is_stable_for_the_same_rule():
    assert lesson_id(SCOPE, FIX) == lesson_id(dict(reversed(list(SCOPE.items()))), FIX)
    assert lesson_id(SCOPE, FIX) != lesson_id(SCOPE, {"property": "columns", "value": "2"})


# --- mining ----------------------------------------------------------------------------------
async def test_a_verified_fix_becomes_a_candidate_lesson_without_tenant_data():
    svc = service()
    events = await svc.learn(FAILING, COLUMNS_3, PASSING, SPEC, "ecommerce", "run-1")
    assert [e.kind for e in events] == ["fix_verified"]
    assert events[0].fix == "columns=3" and events[0].context == SCOPE
    found = await lesson(svc, 0)
    assert found.status == "candidate" and found.confirmations == 1
    assert found.text == (
        "product_grid on storefront pages (ecommerce): 'grid columns are Npx wide, too narrow "
        "for their content' was fixed by columns=3"
    )
    assert found.evidence == ["run-1"]
    for private in ("Ember", "Roast", "autumn", "home baristas"):
        assert private not in found.text and private not in str(found.scope)


async def test_repetition_promotes_and_a_failure_counts_against():
    svc = service()
    assert (await lesson(svc, 2)).status == "validated"
    assert (await lesson(svc, 1)).status == "trusted"
    demoted = await lesson(svc, 0, failures=2)
    assert (demoted.confirmations, demoted.violations, demoted.status) == (3, 2, "candidate")


async def test_a_fix_that_did_not_work_is_a_failed_event():
    svc = service()
    events = await svc.learn(FAILING, COLUMNS_3, FAILING, SPEC, "ecommerce")
    assert [e.kind for e in events] == ["fix_failed"]
    assert (await lesson(svc, 0)).violations == 1


async def test_nothing_is_learned_from_a_failed_fixer_or_a_page_level_patch():
    svc = service()
    failure = FixResult(status="failure", reason="no allowed patch")
    assert await svc.learn(FAILING, failure, FAILING, SPEC, "ecommerce") == []
    density = FixResult(
        status="success", patches=[Patch(target="page", property="density", value="compact")]
    )
    assert await svc.learn(FAILING, density, PASSING, SPEC, "ecommerce") == []
    assert await svc._repository.list_all() == []


async def test_model_found_issues_are_learned_by_dimension_only():
    svc = service()
    calmer = FixResult(
        status="success", patches=[Patch(target="hero", property="variant", value="minimal")]
    )
    before = VerificationResult(status="needs_fix", issues=[CLUTTER])
    [event] = await svc.learn(before, calmer, PASSING, SPEC, "ecommerce")
    assert event.problem == "visual issue"
    [found] = await svc._repository.list_all()
    assert "Ember" not in found.text and "fights" not in found.text


async def test_applied_lessons_are_recorded_as_events():
    svc = service()
    applied = COLUMNS_3.model_copy(update={"source": "lesson", "lesson_ids": ["abc"]})
    events = await svc.learn(FAILING, applied, PASSING, SPEC, "ecommerce")
    assert [e.kind for e in events] == ["fix_verified", "lesson_applied"]
    assert events[1].target == "abc"


# --- back into the agents --------------------------------------------------------------------
async def test_only_confirmed_lessons_reach_the_builder_and_only_in_scope():
    svc = service()
    assert await svc.advise(REQ, DIRECTION, "ecommerce_home") == []  # nothing learned yet
    await lesson(svc, 1)
    assert await svc.advise(REQ, DIRECTION, "ecommerce_home") == []  # a candidate stays quiet
    found = await lesson(svc, 1)
    assert await svc.advise(REQ, DIRECTION, "ecommerce_home") == [describe(found)]
    assert describe(found).endswith("[validated, confirmed 2x]")
    assert await svc.advise(REQ, DIRECTION, "ecommerce_product") == []  # other page type
    assert (
        await svc.advise(REQ.model_copy(update={"domain": "saas"}), DIRECTION, "ecommerce_home")
        == []
    )


async def test_suggest_matches_component_and_problem_of_blocking_issues():
    svc = service()
    found = await lesson(svc, 2)
    assert await svc.suggest(SPEC, FAILING, "ecommerce") == [found]
    other = VerificationResult(status="needs_fix", issues=[CLUTTER])
    assert await svc.suggest(SPEC, other, "ecommerce") == []
    minor = VerificationResult(
        status="pass", issues=[Issue(**{**NARROW.model_dump(), "severity": "minor"})]
    )
    assert await svc.suggest(SPEC, minor, "ecommerce") == []


# --- the fixer -------------------------------------------------------------------------------
def fixer(llm: FakeLLMProvider) -> FixerAgent:
    return FixerAgent(
        llm, default_recipe_registry(), default_component_registry(), default_design_resolver()
    )


def trusted(**overrides: object) -> Lesson:
    base = Lesson(
        id=lesson_id(SCOPE, FIX),
        text="t",
        scope=SCOPE,
        fix=FIX,
        status="trusted",
        confirmations=3,
    )
    return base.model_copy(update=overrides)


async def test_a_trusted_lesson_fixes_without_a_model_call():
    llm = FakeLLMProvider()  # nothing queued: any model call would raise
    fix = await fixer(llm).fix(SPEC, FAILING, [trusted()])
    assert fix.source == "lesson" and fix.lesson_ids == [lesson_id(SCOPE, FIX)]
    assert fix.patches == [Patch(target="featured_products", property="columns", value="3")]
    assert llm.calls == []
    patched = fixer(llm).apply(SPEC, fix)
    grid = patched.find("featured_products")
    assert grid is not None and grid.layout is not None and grid.layout.columns == 3
    default_design_resolver().resolve(patched)


async def test_a_validated_lesson_is_only_a_hint_to_the_model():
    llm = FakeLLMProvider(
        [
            FixerOutput(
                status="success",
                patches=[{"target": "featured_products", "property": "columns", "value": "3"}],
                reason=None,
            )
        ]
    )
    fix = await fixer(llm).fix(SPEC, FAILING, [trusted(status="validated", confirmations=2)])
    assert fix.source == "model"
    user = llm.calls[0][1].content
    assert "Lessons from earlier verified fixes" in user
    assert "was fixed by" in user or "[validated, confirmed 2x]" in user


async def test_lessons_that_do_not_cover_every_issue_defer_to_the_model():
    both = VerificationResult(status="needs_fix", issues=[NARROW, CLUTTER])
    llm = FakeLLMProvider(
        [
            FixerOutput(
                status="success",
                patches=[{"target": "hero", "property": "variant", "value": "centered"}],
                reason=None,
            )
        ]
    )
    fix = await fixer(llm).fix(SPEC, both, [trusted()])
    assert fix.source == "model" and len(llm.calls) == 1


async def test_a_trusted_lesson_whose_patch_does_not_resolve_is_dropped():
    bad = trusted(fix={"property": "columns", "value": "9"})  # columns must be 1-6
    llm = FakeLLMProvider([FixerOutput(status="failure", patches=[], reason="nothing fits")])
    fix = await fixer(llm).fix(SPEC, FAILING, [bad])
    assert fix.status == "failure" and fix.source == "model"
    assert len(llm.calls) == 1


async def test_no_lessons_means_no_lesson_block_in_the_prompt():
    llm = FakeLLMProvider([FixerOutput(status="failure", patches=[], reason="x")])
    await fixer(llm).fix(SPEC, FAILING)
    assert "Lessons from earlier" not in llm.calls[0][1].content


# --- the graph -------------------------------------------------------------------------------
async def test_learning_runs_around_the_fix_loop():
    stub = StubServices(fail_times=1)
    await build_graph(make_services(stub)).ainvoke({"run_id": "r", "user_requirement": "shoes"})
    calls = stub.calls
    assert calls.index("advise") < calls.index("retrieve")
    assert calls.index("suggest") < calls.index("fix")
    assert calls.count("learn") == 1  # once, after the verification that followed the fix
    assert calls.index("learn") > calls.index("fix")


async def test_a_screen_that_passes_first_time_learns_nothing(stub):
    await build_graph(make_services(stub)).ainvoke({"run_id": "r", "user_requirement": "shoes"})
    assert "learn" not in stub.calls and "suggest" not in stub.calls


@pytest.mark.parametrize("status", ["candidate", "validated", "trusted"])
def test_lesson_status_vocabulary(status):
    Lesson(id="x", text="t", status=status)
