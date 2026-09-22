import asyncio
import json
import uuid
from pathlib import Path

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


@cli.command()
def render(
    spec_file: Path = typer.Argument(..., help="JSON file containing a DesignSpec"),
    out: Path = typer.Option(Path("screenshots"), help="Directory for PNG screenshots"),
    reduced_motion: bool = typer.Option(False, help="Render with reduced motion"),
) -> None:
    """Resolve a Design DSL file and render it in a browser. No LLM involved."""
    from app.dsl import default_design_resolver
    from app.models import DesignSpec
    from app.renderer import PlaywrightRenderer

    configure_logging(get_settings().log_level)
    spec = DesignSpec.model_validate_json(spec_file.read_text())
    model = default_design_resolver().resolve(spec, reduced_motion=reduced_motion)
    output = asyncio.run(PlaywrightRenderer(screenshot_dir=out).render_with_findings(model))
    for path in output.result.screenshots.values():
        typer.echo(f"wrote {path}")
    for f in output.findings:
        typer.echo(f"{f.severity.value:<8} {f.dimension.value:<13} {f.target:<22} {f.issue}")
    typer.echo(
        f"{len(output.findings)} deterministic finding(s) in {output.result.render_time_ms:.0f}ms"
    )


@cli.command("dump-spec")
def dump_spec(
    name: str = typer.Argument("saas_landing"), out: Path = typer.Option(Path("spec.json"))
) -> None:
    """Write one of the built-in golden Design DSL fixtures to a file."""
    from tests.fixtures.specs import ALL

    if name not in ALL:
        raise typer.BadParameter(f"unknown fixture '{name}'; choose from {list(ALL)}")
    out.write_text(json.dumps(ALL[name], indent=2))
    typer.echo(f"wrote {out}")


if __name__ == "__main__":  # pragma: no cover
    main()
