# Agentic UI Builder

LLM agents design a compact semantic **Design DSL**; a deterministic engine expands it into
components, layout, tokens, responsive rules, animation and a rendered screenshot.
See `agentic-ui-builder-phase-prompts.md` for the full phase spec.

## Status

Phase 01 (Foundation) complete. Services are interfaces only; the graph runs against stubs in tests.

## Layout

```
app/
  core/       config, logging, exceptions, LLM abstraction (LLMProvider protocol)
  models/     Pydantic models for every stage; models/dsl.py is the central DesignSpec contract
  services/   service + repository Protocols, DI container (Services)
  graph/      AgentState, thin LangGraph nodes, graph builder with conditional routing
  agents/     Phase 07-10, 14, 15 (LLM agents)
  catalog/    Phase 02 component registry
  dsl/        Phase 11 deterministic resolver
  layout/     Phase 04 layout grammar
  animation/  Phase 12 animation engine
  renderer/   Phase 13 renderer
  retrieval/  Phase 06 pgvector retrieval
  verifier/   Phase 14 deterministic checks
  learning/   Phase 16 lessons
```

Rules enforced by `import-linter`: `app.dsl`, `app.layout`, `app.animation`, `app.catalog`,
`app.renderer` may never import the LLM layer.

## Setup

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
docker compose up -d
cp .env.example .env
pytest
lint-imports
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
