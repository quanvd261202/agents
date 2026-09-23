import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

import typer

from app.core.config import get_settings
from app.core.logging import configure_logging

cli = typer.Typer(help="Agentic UI Builder")


@cli.command()
def run(
    requirement: str,
    yes: bool = typer.Option(False, "--yes", "-y", help="Accept every clarifying default"),
    out: Path = typer.Option(Path("runs"), help="Each run writes its screens under out/<run id>"),
) -> None:
    """Run the pipeline for a requirement, answering clarifying questions along the way."""
    settings = get_settings()
    configure_logging(settings.log_level)
    from app.bootstrap import build_services
    from app.graph.builder import build_graph
    from app.graph.checkpoint import checkpointer_for
    from app.graph.summary import format_summary, summarize

    async def go() -> dict[str, Any]:
        svc = await build_services(settings)
        run_id = str(uuid.uuid4())
        async with checkpointer_for(settings) as saver:
            graph = build_graph(svc, saver)
            config = {"configurable": {"thread_id": run_id}}
            payload: dict[str, Any] = {"run_id": run_id, "user_requirement": requirement}
            # The clarifier may not ask twice once answers exist, so this is at most two passes.
            while True:
                state: dict[str, Any] = await graph.ainvoke(payload, config)
                out = state.get("clarifier_output")
                if out is None or out.status != "needs_clarification":
                    return state
                # The checkpoint holds everything else: only the answers travel the second time.
                payload = {"user_answers": _answer(out.questions, yes)}

    state = asyncio.run(go())
    run_dir = out / state["run_id"][:8]
    for screen in state.get("screens") or []:
        if screen.get("errors"):
            typer.echo(f"{screen['screen'].id}: FAILED - {screen['errors'][-1]}", err=True)
            continue
        typer.echo(_save_screen(run_dir, screen))
    summary = summarize(state)
    if state.get("screens"):
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
        if (site := state.get("site_model")) is not None:
            (run_dir / "site.json").write_text(site.model_dump_json())
        typer.echo("\n" + format_summary(summary))
        typer.echo(f"\nwrote {run_dir}/")
    if not summary["accepted"]:
        raise typer.Exit(1)


def _save_screen(run_dir: Path, screen: dict[str, Any]) -> str:
    """Spec, verification and screenshots for one screen; returns a one-line summary."""
    import base64

    run_dir.mkdir(parents=True, exist_ok=True)
    spec, verification = screen["design_spec"], screen["verification_result"]
    sid = spec.screen_id
    (run_dir / f"{sid}.spec.json").write_text(spec.model_dump_json(indent=2, exclude_defaults=True))
    (run_dir / f"{sid}.verification.json").write_text(verification.model_dump_json(indent=2))
    for bp, shot in screen["render_result"].screenshots.items():
        (run_dir / f"{sid}.{bp.value}.png").write_bytes(base64.b64decode(shot))
    severities = [i.severity.value for i in verification.issues]
    issues = ", ".join(f"{severities.count(s)} {s}" for s in ("critical", "major", "minor"))
    fixes = screen.get("iteration", 0)
    return f"{sid} ({spec.recipe}): {verification.status} after {fixes} fix(es); issues: {issues}"


@cli.command()
def view(
    run_dir: Path | None = typer.Argument(None, help="A runs/<id> directory; default: the latest"),
    port: int = typer.Option(8765, help="Local port to serve on"),
) -> None:
    """Open a run's screens, live and interactive, in the browser."""
    import html
    import tempfile
    import webbrowser
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    from app.dsl import default_design_resolver
    from app.models import DesignSpec
    from app.renderer.server import FRONTEND_DIST

    if run_dir is None:
        runs = sorted(Path("runs").glob("*/"), key=lambda p: p.stat().st_mtime)
        if not runs:
            raise typer.BadParameter("no runs yet; `uib run` one first")
        run_dir = runs[-1]
    models = Path(tempfile.mkdtemp(prefix="uib-view-"))
    # A run with a site.json is served as the site: real routes, the visitor's cart, the flow.
    site_json = run_dir / "site.json"
    if site_json.exists():
        _serve_site(site_json, models, port)
        return
    specs = sorted(run_dir.glob("*.spec.json"))
    prebuilt = sorted(run_dir.glob("*.model.json"))  # `uib gallery` output
    if not specs and not prebuilt:
        raise typer.BadParameter(f"no site.json, *.spec.json or *.model.json in {run_dir}")

    resolver = default_design_resolver()
    links = []
    for path in specs:
        spec = DesignSpec.model_validate_json(path.read_text())
        (models / f"{spec.screen_id}.json").write_text(resolver.resolve(spec).model_dump_json())
        name = html.escape(spec.screen_id)
        links.append(
            f'<li><a href="/?model=/models/{name}.json">{name}</a> '
            f"<small>{html.escape(spec.recipe)}</small></li>"
        )
    for path in prebuilt:
        name = html.escape(path.name.removesuffix(".model.json"))
        (models / f"{name}.json").write_text(path.read_text())
        links.append(f'<li><a href="/?model=/models/{name}.json">{name}</a></li>')
    (models / "index.html").write_text(
        f"<!doctype html><title>{html.escape(run_dir.name)}</title>"
        "<body style='font:16px system-ui;margin:40px'>"
        f"<h1>Run {html.escape(run_dir.name)}</h1><ul>{''.join(links)}</ul></body>"
    )

    class Handler(SimpleHTTPRequestHandler):
        def translate_path(self, path: str) -> str:
            if path.startswith("/models/"):
                return str(models / path.split("?")[0].removeprefix("/models/"))
            return super().translate_path(path)

        def log_message(self, *args: object) -> None:
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(FRONTEND_DIST)))
    url = f"http://127.0.0.1:{port}/models/index.html"
    typer.echo(f"serving {run_dir} at {url} (Ctrl-C to stop)")
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def _serve_site(site_json: Path, tmp: Path, port: int) -> None:
    """Serve the bundle with the site injected as window.__uibSite and every extensionless path
    falling back to index.html, so /products/house-blend is the app, not a 404."""
    import webbrowser
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    from app.renderer.server import FRONTEND_DIST

    index = (FRONTEND_DIST / "index.html").read_text(encoding="utf-8")
    (tmp / "site.js").write_text(
        "window.__uibSite = " + site_json.read_text(encoding="utf-8") + ";", encoding="utf-8"
    )
    (tmp / "index.html").write_text(
        index.replace("</head>", '<script src="/site.js"></script></head>', 1), encoding="utf-8"
    )

    class Handler(SimpleHTTPRequestHandler):
        def translate_path(self, path: str) -> str:
            clean = path.split("?")[0]
            if clean in ("/site.js", "/index.html") or "." not in clean.rsplit("/", 1)[-1]:
                return str(tmp / ("site.js" if clean == "/site.js" else "index.html"))
            return super().translate_path(path)

        def log_message(self, *args: object) -> None:
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(FRONTEND_DIST)))
    url = f"http://127.0.0.1:{port}/"
    typer.echo(f"serving {site_json.parent} as a site at {url} (Ctrl-C to stop)")
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


@cli.command()
def gallery(
    component: list[str] = typer.Option([], "--component", "-c", help="Only these component ids"),
    category: str | None = typer.Option(None, help="Only this catalog category"),
    palette: str = typer.Option("espresso", help="Palette to render under"),
    typography: str = typer.Option("editorial_serif", help="Font pairing"),
    radius: str = typer.Option("large", help="Radius personality"),
    theme: str = typer.Option("modern_light", help="Base theme"),
    out: Path = typer.Option(Path("gallery"), help="Screenshots and models land in out/<palette>/"),
) -> None:
    """Render every component x variant with the real renderer and report its checks."""
    from app.catalog import default_component_registry
    from app.dsl import default_design_resolver
    from app.models.dsl import SectionSpec
    from app.renderer import PlaywrightRenderer, StaticServer

    configure_logging("WARNING")
    comps = [
        c
        for c in default_component_registry()
        if (not component or c.id in component) and (category is None or c.category == category)
    ]
    if not comps:
        raise typer.BadParameter("no component matches")
    resolver = default_design_resolver()
    target = out / palette
    target.mkdir(parents=True, exist_ok=True)

    async def go() -> int:
        blocking = 0
        with StaticServer() as server:
            renderer = PlaywrightRenderer(server=server, screenshot_dir=target)
            for comp in comps:
                model = resolver.preview(
                    [
                        SectionSpec(id=f"{comp.id}-{v}", type=comp.id, variant=v)
                        for v in comp.variants
                    ],
                    screen_id=comp.id,
                    theme=theme,
                    palette=palette,
                    typography=typography,
                    radius=radius,
                )
                (target / f"{comp.id}.model.json").write_text(model.model_dump_json())
                findings = (await renderer.render_with_findings(model)).findings
                bad = [
                    f
                    for f in findings
                    if f.severity == "critical"
                    or (f.severity == "major" and f.dimension == "accessibility")
                ]
                blocking += len(bad)
                mark = "FAIL" if bad else "ok  "
                typer.echo(
                    f"{mark} {comp.id} ({len(comp.variants)} variants, {len(findings)} findings)"
                )
                for f in bad:
                    typer.echo(f"       [{f.severity.value}] {f.target}: {f.issue}")
        return blocking

    blocking = asyncio.run(go())
    typer.echo(f"\n{len(comps)} components -> {target}/   (uib view {target})")
    if blocking:
        raise typer.Exit(1)


@cli.command()
def lessons(
    status: str | None = typer.Option(None, help="Only candidate, validated or trusted"),
) -> None:
    """List what the fix loop has learned: each rule with its status and confirmations."""
    from app.learning.factory import build_lesson_repository

    settings = get_settings()
    configure_logging("WARNING")

    async def go() -> list[Any]:
        return await (await build_lesson_repository(settings)).list_all()

    rows = [x for x in asyncio.run(go()) if status is None or x.status == status]
    for x in rows:
        typer.echo(
            f"{x.status:<9} {x.confirmations:>3}x confirmed {x.violations:>2}x violated  {x.text}"
        )
    typer.echo(f"\n{len(rows)} lesson(s)")


@cli.command()
def stages(
    run: str = typer.Argument(..., help="A run id, or a runs/<id> directory with a summary.json"),
) -> None:
    """List the persisted stages of a run, in order, with what each one produced."""
    from app.db import build_run_repository

    settings = get_settings()
    configure_logging("WARNING")
    path = Path(run)
    run_id = json.loads((path / "summary.json").read_text())["run_id"] if path.is_dir() else run

    async def go() -> list[tuple[str, dict[str, object]]]:
        return await (await build_run_repository(settings)).stages(run_id)

    rows = asyncio.run(go())
    for stage, payload in rows:
        typer.echo(f"{stage:<28} {', '.join(payload) or '-'}")
    typer.echo(f"\n{len(rows)} stage(s) for run {run_id}")


def _answer(questions: list[Any], accept_defaults: bool) -> dict[str, str]:
    answers: dict[str, str] = {}
    for q in questions:
        default = q.default or (q.options[0] if q.options else "")
        if accept_defaults:
            answers[q.question] = default
            continue
        typer.echo(q.question)
        for i, option in enumerate(q.options, 1):
            typer.echo(f"  {i}. {option}")
        reply = typer.prompt("Answer (number or text)", default=default)
        answers[q.question] = (
            q.options[int(reply) - 1]
            if reply.isdigit() and 0 < int(reply) <= len(q.options)
            else reply
        )
    return answers


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


@cli.command()
def retrieve(
    product: str = typer.Argument(..., help="What is being built"),
    domain: str = typer.Option("saas", help="Product domain, e.g. ecommerce or saas"),
    style: str = typer.Option("premium_modern", help="Visual style from the design direction"),
    recipe: str = typer.Option("saas_landing", help="Recipe the director chose"),
    pg: bool = typer.Option(False, "--pg", help="Use pgvector instead of the in-memory index"),
) -> None:
    """Show the compact context retrieval would hand the Design Builder."""
    from app.models.direction import DesignDirection, ScreenDirection
    from app.models.requirements import ClarifiedRequirements
    from app.retrieval import PgVectorRetrievalRepository, build_retrieval_service

    settings = get_settings()
    configure_logging(settings.log_level)

    async def run() -> None:
        repository = None
        if pg:
            from app.db import build_session_factory

            repository = PgVectorRetrievalRepository(
                build_session_factory(settings.database_url), settings.embedding_dimensions
            )
            await repository.create_schema()
        service = await build_retrieval_service(settings, repository)
        ctx = await service.retrieve(
            ClarifiedRequirements(
                product=product, domain=domain, target_audience="general", primary_goal=product
            ),
            DesignDirection(
                visual_style=style,
                theme="modern_light",
                typography="modern_sans",
                radius="large",
                layout_strategy="grid",
                animation="subtle",
                screens=[ScreenDirection(screen_id="page", recipe=recipe)],
            ),
            recipe,
        )
        for label, lines in (
            ("recipes", ctx.recipes),
            ("components", ctx.components),
            ("layouts", ctx.layouts),
        ):
            typer.echo(f"\n{label}:")
            for line in lines:
                typer.echo(f"  {line}")
        typer.echo(f"\n~{ctx.estimated_tokens} tokens of context")

    asyncio.run(run())


if __name__ == "__main__":  # pragma: no cover
    main()
