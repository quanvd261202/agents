from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.llm import FakeLLMProvider
from app.models import (
    ClarifiedRequirements,
    ClarifierOutput,
    DesignDirection,
    DesignSpec,
    FixResult,
    Issue,
    Patch,
    RenderModel,
    RenderNode,
    RenderResult,
    ScreenDirection,
    ScreenPlan,
    UXPlan,
    VerificationResult,
)
from app.retrieval.models import RetrievedContext
from app.services.container import Services

REQ = ClarifiedRequirements(
    product="shoe store", domain="ecommerce", target_audience="general", primary_goal="sell shoes"
)
SPEC = DesignSpec(
    screen_id="home",
    recipe="saas_landing",
    visual_style="modern",
    theme="modern_light",
    sections=[{"id": "hero_01", "type": "hero"}],
)


class StubServices:
    """Scripted verifier: fails `fail_times` before passing (counted across all screens)."""

    def __init__(
        self,
        fail_times: int = 0,
        fixer_ok: bool = True,
        ready: bool = True,
        screens: tuple[str, ...] = ("home",),
    ) -> None:
        self.fail_times, self.fixer_ok, self.ready = fail_times, fixer_ok, ready
        self.screens = screens
        self.briefs: list[str] = []
        self.calls: list[str] = []

    async def clarify(self, requirement, answers):
        self.calls.append("clarify")
        if not self.ready:
            return ClarifierOutput(status="needs_clarification", questions=[{"question": "Who?"}])
        return ClarifierOutput(status="ready", clarified_requirements=REQ)

    async def plan(self, req, brief=""):
        self.calls.append("plan")
        self.briefs.append(brief)
        return UXPlan(
            product="x",
            user_goals=["buy"],
            journey=["a"],
            screens=[ScreenPlan(id=s, purpose="d") for s in self.screens],
        )

    async def direct(self, req, plan, brief=""):
        self.calls.append("direct")
        return DesignDirection(
            visual_style="m",
            theme="modern_light",
            typography="s",
            radius="l",
            layout_strategy="g",
            animation="subtle",
            screens=[ScreenDirection(screen_id=s, recipe="saas_landing") for s in self.screens],
        )

    async def retrieve(self, req, direction, recipe, lessons=None):
        self.calls.append("retrieve")
        return RetrievedContext(
            components=["hero", "cta"], layouts=["stack"], recipes=["saas_landing"]
        )

    async def build(self, req, screen, direction, ctx):
        self.calls.append("build")
        return SPEC.model_copy(update={"screen_id": screen.id})

    def resolve(self, spec, *, reduced_motion=False):
        self.calls.append("resolve")
        return RenderModel(
            screen_id=spec.screen_id,
            theme=spec.theme,
            root=RenderNode(id="root", semantic_type="page", implementation="Page"),
        )

    async def render(self, model):
        self.calls.append("render")
        return RenderResult(html="<div/>")

    async def verify(self, spec, model, result):
        self.calls.append("verify")
        if self.fail_times > 0:
            self.fail_times -= 1
            return VerificationResult(
                status="needs_fix",
                issues=[
                    Issue(
                        severity="major",
                        dimension="layout",
                        target="hero_01",
                        issue="x",
                        suggestion="y",
                    )
                ],
            )
        return VerificationResult(status="pass")

    async def fix(self, spec, verification):
        self.calls.append("fix")
        if not self.fixer_ok:
            return FixResult(status="failure", reason="cannot")
        return FixResult(
            status="success", patches=[Patch(target="hero_01", property="variant", value="split")]
        )

    def apply(self, spec, fix):
        return spec


def make_services(stub: StubServices, max_iter: int = 3) -> Services:
    settings = Settings(llm_provider="fake", max_design_iterations=max_iter, _env_file=None)
    return Services(
        settings=settings,
        llm=FakeLLMProvider(),
        clarifier=stub,
        planner=stub,
        director=stub,
        retrieval=stub,
        builder=stub,
        resolver=stub,
        renderer=stub,
        verifier=stub,
        fixer=stub,
    )


@pytest.fixture
def stub() -> StubServices:
    return StubServices()
