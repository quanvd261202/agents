"""Dependency injection boundary. Graph nodes receive this; nothing else instantiates services."""

from dataclasses import dataclass

from app.core.config import Settings
from app.core.llm import LLMProvider
from app.services.interfaces import (
    ClarifierService,
    DesignBuilderService,
    DesignDirectorService,
    DesignResolverService,
    FixerService,
    PlannerService,
    RendererService,
    RetrievalService,
    VerifierService,
)


@dataclass
class Services:
    settings: Settings
    llm: LLMProvider
    clarifier: ClarifierService
    planner: PlannerService
    director: DesignDirectorService
    retrieval: RetrievalService
    builder: DesignBuilderService
    resolver: DesignResolverService
    renderer: RendererService
    verifier: VerifierService
    fixer: FixerService
