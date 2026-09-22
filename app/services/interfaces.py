"""Service boundaries. LangGraph nodes call these; implementations live in their own packages."""

from typing import Protocol

from app.models import (
    ClarifiedRequirements,
    ClarifierOutput,
    DesignDirection,
    DesignSpec,
    FixResult,
    RenderModel,
    RenderResult,
    UXPlan,
    VerificationResult,
)
from app.retrieval.models import RetrievedContext


class ClarifierService(Protocol):
    async def clarify(self, requirement: str, answers: dict[str, str]) -> ClarifierOutput: ...


class PlannerService(Protocol):
    async def plan(self, req: ClarifiedRequirements) -> UXPlan: ...


class DesignDirectorService(Protocol):
    async def direct(self, req: ClarifiedRequirements, plan: UXPlan) -> DesignDirection: ...


class RetrievalService(Protocol):
    async def retrieve(
        self,
        req: ClarifiedRequirements,
        direction: DesignDirection,
        lessons: list[str] | None = None,
    ) -> RetrievedContext: ...


class DesignBuilderService(Protocol):
    async def build(
        self,
        req: ClarifiedRequirements,
        plan: UXPlan,
        direction: DesignDirection,
        context: RetrievedContext,
    ) -> DesignSpec: ...


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
    async def fix(self, spec: DesignSpec, verification: VerificationResult) -> FixResult: ...

    def apply(self, spec: DesignSpec, fix: FixResult) -> DesignSpec: ...
