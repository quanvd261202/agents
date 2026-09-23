"""Service boundaries. LangGraph nodes call these; implementations live in their own packages."""

from collections.abc import Sequence
from typing import Protocol

from app.models import (
    ClarifiedRequirements,
    ClarifierOutput,
    DesignDirection,
    DesignSpec,
    FixResult,
    LearningEvent,
    Lesson,
    RenderModel,
    RenderResult,
    ScreenPlan,
    UXPlan,
    VerificationResult,
)
from app.retrieval.models import RetrievedContext


class ClarifierService(Protocol):
    async def clarify(self, requirement: str, answers: dict[str, str]) -> ClarifierOutput: ...


class PlannerService(Protocol):
    async def plan(self, req: ClarifiedRequirements, brief: str = "") -> UXPlan: ...


class DesignDirectorService(Protocol):
    async def direct(
        self, req: ClarifiedRequirements, plan: UXPlan, brief: str = ""
    ) -> DesignDirection: ...


class RetrievalService(Protocol):
    async def retrieve(
        self,
        req: ClarifiedRequirements,
        direction: DesignDirection,
        recipe: str,
        lessons: list[str] | None = None,
    ) -> RetrievedContext: ...


class DesignBuilderService(Protocol):
    async def build(
        self,
        req: ClarifiedRequirements,
        screen: ScreenPlan,
        direction: DesignDirection,
        context: RetrievedContext,
    ) -> DesignSpec: ...


class CopywriterService(Protocol):
    async def write(
        self,
        req: ClarifiedRequirements,
        screen: ScreenPlan,
        direction: DesignDirection,
        spec: DesignSpec,
        brief: str = "",
    ) -> DesignSpec: ...


class ImageryService(Protocol):
    """Sources photographs for the spec's image slots. Network, never an LLM."""

    async def illustrate(self, spec: DesignSpec) -> DesignSpec: ...


class DesignResolverService(Protocol):
    """Deterministic. Must not call an LLM."""

    def resolve(self, spec: DesignSpec, *, reduced_motion: bool = False) -> RenderModel: ...


class RendererService(Protocol):
    async def render(self, model: RenderModel) -> RenderResult: ...


class VerifierService(Protocol):
    async def verify(
        self, spec: DesignSpec, model: RenderModel, result: RenderResult
    ) -> VerificationResult: ...


class FixerService(Protocol):
    async def fix(
        self,
        spec: DesignSpec,
        verification: VerificationResult,
        lessons: Sequence[Lesson] = (),
    ) -> FixResult: ...

    def apply(self, spec: DesignSpec, fix: FixResult) -> DesignSpec: ...


class LearningService(Protocol):
    """Phase 16. Deterministic: mines lessons from verified fixes and hands confirmed ones back."""

    async def advise(
        self, req: ClarifiedRequirements, direction: DesignDirection, recipe: str
    ) -> list[str]: ...

    async def suggest(
        self, spec: DesignSpec, verification: VerificationResult, domain: str
    ) -> list[Lesson]: ...

    async def learn(
        self,
        before: VerificationResult,
        fix: FixResult,
        after: VerificationResult,
        spec: DesignSpec,
        domain: str,
        run_id: str = "",
    ) -> list[LearningEvent]: ...
