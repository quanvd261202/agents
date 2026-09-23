"""Wires concrete services."""

from app.agents import (
    ClarifierAgent,
    CopywriterAgent,
    DesignBuilderAgent,
    DirectorAgent,
    FixerAgent,
    PlannerAgent,
    VerifierAgent,
)
from app.animation import default_animation_registry
from app.catalog import default_component_registry
from app.core.config import Settings
from app.core.llm import build_llm_provider
from app.dsl import default_design_resolver
from app.imagery import Illustrator, build_image_provider
from app.recipes import default_recipe_registry
from app.renderer import PlaywrightRenderer
from app.retrieval import build_retrieval_service
from app.services.container import Services
from app.tokens import default_theme_registry


async def build_services(settings: Settings) -> Services:  # noqa: D103
    key = (
        settings.anthropic_api_key
        if settings.llm_provider == "anthropic"
        else settings.openai_api_key
    )
    secret = key.get_secret_value() if key else None
    llm = build_llm_provider(
        settings.llm_provider, settings.llm_model, settings.llm_base_url, secret
    )
    vision = (
        build_llm_provider(
            settings.llm_provider, settings.verifier_model, settings.llm_base_url, secret
        )
        if settings.verifier_model
        else llm
    )
    components = default_component_registry()
    recipes = default_recipe_registry()
    animations = default_animation_registry()
    resolver = default_design_resolver()
    return Services(
        settings=settings,
        llm=llm,
        clarifier=ClarifierAgent(llm, recipes, settings.max_clarifier_questions),
        planner=PlannerAgent(llm, recipes),
        director=DirectorAgent(llm, default_theme_registry(), recipes, animations),
        retrieval=await build_retrieval_service(settings),
        builder=DesignBuilderAgent(llm, recipes, components, animations),
        copywriter=CopywriterAgent(llm, components),
        imagery=Illustrator(
            build_image_provider(
                settings.image_provider,
                settings.pexels_api_key.get_secret_value() if settings.pexels_api_key else None,
            )
        ),
        resolver=resolver,
        renderer=PlaywrightRenderer(),
        verifier=VerifierAgent(vision, recipes),
        fixer=FixerAgent(llm, recipes, components, resolver),
    )
