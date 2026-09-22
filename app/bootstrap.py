"""Wires concrete services. Phases 02-16 replace the NotImplemented stubs."""

from typing import Any

from app.core.config import Settings
from app.core.llm import build_llm_provider
from app.services.container import Services


class _NotWired:
    def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
        raise NotImplementedError(f"service not wired yet: {name}")


def build_services(settings: Settings) -> Services:  # noqa: D103
    llm = build_llm_provider(settings.llm_provider, settings.llm_model)
    nw: Any = _NotWired()
    return Services(
        settings=settings,
        llm=llm,
        clarifier=nw,
        planner=nw,
        director=nw,
        retrieval=nw,
        builder=nw,
        resolver=nw,
        renderer=nw,
        verifier=nw,
        fixer=nw,
    )
