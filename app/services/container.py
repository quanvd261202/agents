"""Dependency injection boundary. Graph nodes receive this; nothing else instantiates services."""

from dataclasses import dataclass

from app.core.config import Settings
from app.core.llm import LLMProvider
from app.services.interfaces import (
    ClarifierService,
    ContentModelService,
    CopywriterService,
    DesignBuilderService,
    DesignDirectorService,
    DesignResolverService,
    FixerService,
    FlowCheckService,
    FlowFixerService,
    ImageryService,
    LearningService,
    PlannerService,
    RendererService,
    RetrievalService,
    VerifierService,
)
from app.services.repositories import RunRepository


@dataclass
class Services:
    settings: Settings
    llm: LLMProvider
    runs: RunRepository
    clarifier: ClarifierService
    planner: PlannerService
    director: DesignDirectorService
    content: ContentModelService
    retrieval: RetrievalService
    builder: DesignBuilderService
    copywriter: CopywriterService
    imagery: ImageryService
    resolver: DesignResolverService
    renderer: RendererService
    verifier: VerifierService
    fixer: FixerService
    learning: LearningService
    flow: FlowCheckService
    flow_fixer: FlowFixerService
