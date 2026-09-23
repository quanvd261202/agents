# Agentic UI Builder

LLM agents design a compact semantic **Design DSL**; a deterministic engine expands it into
components, layout, tokens, responsive rules, animation and a rendered screenshot.
See `agentic-ui-builder-phase-prompts.md` for the full phase spec.

## Status

Phases 01-15 complete and running end to end: foundation, all static registries, retrieval, the
LLM agent chain (Clarifier -> UX Planner -> Design Director -> Compact Design Builder ->
Copywriter), imagery, the deterministic resolver (`DesignSpec` -> `RenderModel`), the browser
renderer with deterministic checks, the screenshot Verifier and the targeted Fixer. Learning (16)
is next.

    uib run -y "An online shop selling specialty coffee beans and loose-leaf tea"

writes each screen's spec, verification and screenshots under `runs/<run id>/`. Without `-y` the
clarifying questions are asked interactively.

**Verify/fix.** The verifier sees every breakpoint's screenshot plus the renderer's deterministic
findings, which are authoritative. Status is derived, not chosen by the model: any critical or
major issue means `needs_fix`; minor issues are reported only. The fixer returns small patches
(`variant`, `type`, `animation`, `layout`, `columns`, `remove`, page `density`) limited to the
sections an issue names, and a patch is accepted only if the patched spec still resolves. After
`UIB_MAX_DESIGN_ITERATIONS` fixes a screen finalizes with its open issues rather than erroring.

**Rate limits.** Screenshots dominate token use. Set `UIB_VERIFIER_MODEL=gpt-4o` when the main
model is gpt-4o-mini: mini bills image tiles ~30x heavier (about 60k vs 2k input tokens per verify),
which is slower, dearer and trips tokens-per-minute limits. `UIB_MAX_PARALLEL_SCREENS` (default 2)
caps how many screens run at once. A screen that fails (rate limit, invalid output after repairs)
is reported on its own; the others still finish.

**Design system (M6).** The Director picks brand axes by name, never raw values: a `palette`
(11, each WCAG-AA checked when the registry loads), `typography` (9 self-hosted font pairings with
a fluid `clamp()` type scale) and `radius` (corner personality). They flow through `DesignSpec` to
CSS variables, which Tailwind v4 reads, so every component follows the brand. Section tones
(`inverse`, `accent`...) re-scope the colour roles so anything inside a dark band stays readable.

**Component library (M7).** 76 components, 206 variants, in `frontend/src/sections/<module>.tsx`
with catalog entries in `app/catalog/data/<module>.py`, built on shared primitives (`src/ui`:
Radix, Embla, lucide). Conventions: `frontend/src/sections/README.md`.

    uib gallery --category commerce --palette noir --typography luxe_serif --radius none
    uib view gallery/noir

renders every component x variant under any brand with the renderer's checks.
`tests/integration/test_design_system.py` holds the exit criteria: one page reads as five
distinct brands and stays accessible; every variant renders cleanly under a light and a dark brand.

**Motion (M8).** The Director sets page intensity; the Builder may pick one animation per
section; `app/dsl/choreography.py` expands that deterministically by component role (a hero's
headline reveals and its image settles on scroll, a grid staggers in and its cards lift, a stats
band counts up) and enforces a per-page budget: subtle pages get no attention-grabbing motion,
moderate and expressive pages cap headline reveals, scroll-linked effects, magnetic CTAs, tilt,
stacking and ambient loops, earliest sections first. The frontend runtime (`src/motion/`) executes
the behaviours through markers the primitives set, so every component moves without knowing it.
Add-to-cart flights, sliding option chips, tab crossfades and toggle pops are page-wide. Reduced
motion runs none of it; the renderer dispatches `uib:settle` so captures show every section at
rest, and the checks report layout shift, main-thread blocking and more than four continuous loops.

**Content (M10).** The Builder owns structure; a Copywriter then writes the words for each screen.
It is shown the built sections with every slot the component can show (and its format note) and
returns copy per slot, plus `items` for sections that list products, which become `product_card`
children with real names, notes, prices and badges. It can only add `content`: the output schema
has no types, variants or layouts. Copy lands in `SectionSpec.content`, the same channel recipe
defaults and the frontend's `prop(node, slot, fallback)` already use, so a slot the writer skips
keeps the component's own default. Placeholder text (lorem ipsum, "Product 1") and unknown slots
are handed back to the model with the exact error.

Image slots (`media`, `image`) hold a description of the photograph to find, not a keyword. After
the copy is written the imagery service searches a stock library (Pexels, `PEXELS_API_KEY`) once
per distinct description, keeps the results for the run, never repeats a photo on one page and
stores the URLs in `SectionSpec.images` so a saved spec re-renders identically. The renderer waits
for the photographs before it captures. A description that finds nothing, or a provider outage,
leaves the art-directed placeholder in place: a missing photo never fails a screen. Set
`UIB_IMAGE_PROVIDER=none` to keep the placeholders.

Every planned screen is built. Clarifier, Planner and Director run once per product; the Director
assigns each planned screen a recipe (`DesignDirection.screens`), and the graph fans out one
retrieval -> build -> write -> illustrate -> resolve -> render -> verify/fix subgraph per screen.
Results land in
`state["screens"]` in plan order, each with its own fix loop. Ecommerce is covered end to end by
`ecommerce_home`, `ecommerce_listing`, `ecommerce_product`, `ecommerce_cart` and
`ecommerce_checkout`.

Motion has one owner per level: the Design Director sets the page-level strategy (its intensity
comes from `PAGE_ANIMATION_ALIASES`, the same table the resolver expands it with) and the Builder
picks per-section motion from each component's `animation_capabilities`. The Builder's output
schema carries sections only, so `screen_id`, `recipe`, `theme`, `visual_style`, `density` and page
animation stay derived from upstream state rather than restated by the model.

Each agent gets two repair retries: its output is checked against the registries, and an unknown
recipe, theme, variant, section slot or unsupported animation is handed back to the model with the
exact error before that screen fails. A required slot with only one allowed component (usually the
footer) is filled in deterministically rather than sent back.

**Providers.** OpenAI is the default for both chat and embeddings; Anthropic is also wired.
Set `UIB_LLM_PROVIDER` / `UIB_EMBEDDING_PROVIDER`. Leaving `UIB_LLM_MODEL` empty takes the
provider default. `UIB_EMBEDDING_PROVIDER=hashing` runs retrieval offline with no API key.
Photographs come from `UIB_IMAGE_PROVIDER` (`pexels` with a free `PEXELS_API_KEY`, `fake` for
deterministic test URLs, `none` for the placeholders).

## Layout

```
app/
  core/       config, logging, exceptions, LLM abstraction (LLMProvider protocol)
  models/     Pydantic models for every stage; models/dsl.py is the central DesignSpec contract
  services/   service + repository Protocols, DI container (Services)
  graph/      AgentState, thin LangGraph nodes, graph builder with conditional routing
  agents/     Phase 07-10, 14, 15 (LLM agents) and the M10 Copywriter
  imagery/    M10 stock photo providers (Pexels, fake) and the service that fills image slots
  catalog/    Phase 02 semantic component registry + implementation mappings (data/components.py)
  tokens/     Phase 03 themes with inheritance, TokenResolver (intent -> CSS variables)
  layout/     Phase 04 layout grammar: LayoutSpec, nesting/ratio/column validation, responsive resolver
  recipes/    Phase 05 page recipes, RecipeValidator (required sections, reorder groups), RecipeResolver
  animation/  Phase 12 animation vocabulary, intensity presets, MotionAnimationEngine, reduced motion
  dsl/        Phase 11 deterministic resolver (DesignSpec -> RenderModel), no LLM
  renderer/   Phase 13 static server, Playwright driver, deterministic DOM checks (checks.js)
  retrieval/  Phase 06 embeddings (OpenAI + offline hashing), in-memory and pgvector stores,
              registry indexer, filtered search, context budget
  db/         async SQLAlchemy engine and session factory
  verifier/   Phase 14 deterministic checks
  learning/   Phase 16 lessons
```

Rules enforced by `import-linter`: `app.dsl`, `app.layout`, `app.animation`, `app.catalog`, `app.tokens`,
`app.recipes`, `app.renderer`, `app.imagery` may never import the LLM layer.

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

Inspect what retrieval would send the design agent (no API key needed with the hashing provider):

```bash
UIB_EMBEDDING_PROVIDER=hashing uib retrieve "running shoe store" --domain ecommerce
uib retrieve "premium analytics dashboard" --domain saas --recipe dashboard --pg
```

Render a Design DSL file without any LLM:

```bash
uib dump-spec ecommerce_product --out spec.json
uib render spec.json --out screenshots
```

## Graph

```
START → clarifier ─(needs_clarification)→ END
              └─(ready)→ planner → design_director ─(one Send per planned screen)→ screen → END

screen:  retrieval → design_builder → copywriter → imagery → resolver → renderer → verifier ─(pass)→ finalize
                                                  └─(needs_fix, budget left)→ fixer ─(success)→ resolver
                                                  └─(needs_fix, budget spent)→ finalize
                                                                     fixer ─(failure)→ finalize
```

Fixes per screen are capped by `UIB_MAX_DESIGN_ITERATIONS` (default 3).
