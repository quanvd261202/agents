import asyncio
import uuid

import typer

from app.core.config import get_settings
from app.core.logging import configure_logging

cli = typer.Typer(help="Agentic UI Builder")


@cli.command()
def run(requirement: str) -> None:
    """Run the pipeline for a requirement (services wired in later phases)."""
    settings = get_settings()
    configure_logging(settings.log_level)
    from app.bootstrap import build_services
    from app.graph.builder import build_graph

    graph = build_graph(build_services(settings))
    state = asyncio.run(
        graph.ainvoke(
            {"run_id": str(uuid.uuid4()), "user_requirement": requirement, "iteration": 0}
        )
    )
    typer.echo(state.get("clarifier_output"))


def main() -> None:
    cli()
