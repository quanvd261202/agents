# Agentic UI Builder

LLM agents design a compact semantic **Design DSL**; a deterministic engine expands it into
components, layout, tokens, responsive rules, animation and a rendered screenshot.
See `agentic-ui-builder-phase-prompts.md` for the full phase spec.

## Status

Phases 01-05 and 11-13 complete: foundation, all static registries, the deterministic resolver
(`DesignSpec` -> `RenderModel`) and the browser renderer with deterministic screenshot checks.
Agents (Phases 07-10, 14-15), retrieval (06) and learning (16) are next.

## Layout

```
app/
  core/       config, logging, exceptions, LLM abstraction (LLMProvider protocol)
  models/     Pydantic models for every stage; models/dsl.py is the central DesignSpec contract
  services/   service + repository Protocols, DI container (Services)
  graph/      AgentState, thin LangGraph nodes, graph builder with conditional routing
  agents/     Phase 07-10, 14, 15 (LLM agents)
  catalog/    Phase 02 semantic component registry + implementation mappings (data/components.py)
  tokens/     Phase 03 themes with inheritance, TokenResolver (intent -> CSS variables)
  layout/     Phase 04 layout grammar: LayoutSpec, nesting/ratio/column validation, responsive resolver
  recipes/    Phase 05 page recipes, RecipeValidator (required sections, reorder groups), RecipeResolver
  animation/  Phase 12 animation vocabulary, intensity presets, MotionAnimationEngine, reduced motion
  dsl/        Phase 11 deterministic resolver (DesignSpec -> RenderModel), no LLM
  renderer/   Phase 13 static server, Playwright driver, deterministic DOM checks (checks.js)
  retrieval/  Phase 06 pgvector retrieval
  verifier/   Phase 14 deterministic checks
  learning/   Phase 16 lessons
```

Rules enforced by `import-linter`: `app.dsl`, `app.layout`, `app.animation`, `app.catalog`, `app.tokens`,
`app.recipes`, `app.renderer` may never import the LLM layer.

All registries share `app.core.registry.BaseRegistry` (register/get/exists/list/filter, duplicate-id guard).

## Frontend renderer

`frontend/` is a Vite + React + Motion app and a pure function of the `RenderModel`. A tree walker
maps each node's `implementation` name to a React component. Pure containers (`Page`, `Main`) apply
the resolved layout to their own element; every other component receives the resolved column count
and grid tracks for the current breakpoint and applies them to its own collection, so a section is
never boxed inside a grid track that starves the grid within it. Unknown implementations and
component crashes surface as structured, visible errors, never as silent fallback UI.

The layout resolver emits a complete snapshot per breakpoint rather than deltas, so the renderer
never merges cascading overrides and a collapse declared at one breakpoint cannot leak into a
larger one.

```bash
npm --prefix frontend install
npm --prefix frontend run build     # produces frontend/dist, served by app.renderer.StaticServer
```

## Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
docker compose up -d
cp .env.example .env
playwright install chromium
pytest                    # unit tests only when the bundle or playwright is missing
pytest -m integration     # renders every recipe in a real browser
lint-imports
```

Render a Design DSL file without any LLM:

```bash
uib dump-spec ecommerce_product --out spec.json
uib render spec.json --out screenshots
```

## Graph

```
START → clarifier ─(needs_clarification)→ END
              └─(ready)→ planner → design_director → retrieval → design_builder
                → resolver → renderer → verifier ─(pass)→ finalize → END
                                             └─(needs_fix)→ fixer ─(success)→ resolver
                                                                 └─(failure)→ finalize
```

Iterations are capped by `UIB_MAX_DESIGN_ITERATIONS` (default 3).
