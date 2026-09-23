# Agentic UI Builder — Phase-by-Phase Implementation Prompts

This directory contains implementation prompts for building a Python + LangChain/LangGraph agentic UI/UX generation system from scratch.

## Core Architecture

```text
User Requirement
      ↓
Clarifier
      ↓
Planner
      ↓
Design Director
      ↓
Component/Layout Retrieval
      ↓
Design Builder
      ↓
Deterministic Design Engine
 ┌─────────────────────────────┐
 │ Recipe Resolver             │
 │ Component Resolver          │
 │ Layout Resolver             │
 │ Token Resolver              │
 │ Animation Resolver          │
 │ Responsive Resolver         │
 └──────────────┬──────────────┘
                ↓
             Renderer
                ↓
            Screenshot
                ↓
             Verifier
                ↓
              Fixer
                ↓
        Deterministic Engine
                ↓
             Finalize
                ↓
             Learning
```

## Fundamental Principle

The LLM is the **designer**, not the implementation engine.

The LLM generates a compact semantic Design DSL.

Deterministic application code expands the DSL into:

- components
- layout
- design tokens
- responsive behavior
- animation
- rendering instructions

Never ask the LLM to generate large React/CSS/Tailwind/Motion implementations when deterministic code can perform the expansion.

---

# Phase 01 — Foundation

## Goal

Build the project skeleton for an agentic UI builder using:

- Python 3.12+
- LangChain
- LangGraph
- Pydantic
- PostgreSQL
- pgvector
- structured LLM outputs
- async execution where appropriate

Do NOT implement the complete system in this phase.

## Architecture

Create:

```text
app/
├── agents/
├── catalog/
├── dsl/
├── layout/
├── animation/
├── renderer/
├── retrieval/
├── verifier/
├── learning/
└── graph/
```

Create:

- configuration management
- LLM abstraction
- LangGraph state
- common exceptions
- logging
- dependency injection boundaries
- repository interfaces
- service interfaces

Use Pydantic models for structured agent input/output.

Do not pass untyped dictionaries between agents.

## Agent State

Create an extensible graph state containing:

- user_requirement
- clarified_requirements
- ux_plan
- design_direction
- design_spec
- resolved_design
- render_result
- verification_result
- fix_result
- learning_events
- iteration
- errors

## LLM abstraction

Create an abstraction similar to:

```python
class LLMProvider(Protocol):
    async def invoke_structured(...): ...
    async def invoke_text(...): ...
```

Do not hardcode a provider throughout the application.

## Initial LangGraph

```text
START
 ↓
clarifier
 ↓
planner
 ↓
design_director
 ↓
design_builder
 ↓
resolver
 ↓
renderer
 ↓
verifier
 ↓
fixer
 ↓
END
```

Nodes should delegate business logic to services.

Do not put business logic directly inside LangGraph node functions.

## Deliverables

1. Project structure
2. pyproject.toml
3. Pydantic models
4. AgentState
5. LLM abstraction
6. LangGraph skeleton
7. Unit-test structure
8. README

Do not implement component resolution yet.

---

# Phase 02 — Semantic Component Catalog

## Objective

Create a semantic component registry.

The LLM should select components such as:

- hero
- product_card
- product_grid
- pricing_table
- stats
- activity_feed
- settings_form
- dashboard_sidebar
- data_table
- testimonial_grid
- feature_bento
- faq
- cta
- footer

The LLM must NOT need to understand raw implementation components such as:

- div
- flex
- grid
- motion.div
- Card
- Button
- Dialog

## ComponentDefinition

Create a strongly typed model containing:

- id
- category
- description
- capabilities
- supported_domains
- supported_layouts
- variants
- slots
- allowed_children
- responsive_behavior
- implementation
- animation_capabilities
- design_metadata

Example:

```json
{
  "id": "product_card",
  "category": "commerce",
  "capabilities": [
    "product_summary",
    "commerce",
    "responsive"
  ],
  "variants": [
    "standard",
    "premium",
    "compact"
  ]
}
```

## Implementation Mapping

Separate semantic identity from implementation.

Example:

```text
product_card
    ↓
Card
Image
Badge
Button
Motion
```

The LLM only sees:

```text
product_card
```

The resolver knows how to implement it.

## Registry

Implement:

```python
ComponentRegistry
```

with:

- register()
- get()
- exists()
- list()
- search()
- get_by_category()
- get_by_capability()

Prevent duplicate component IDs.

## Validation

Reject:

- unknown component IDs
- invalid variants
- invalid slots
- invalid child components

## Tests

Test:

- registration
- duplicate registration
- lookup
- unknown component
- variant validation
- capability filtering
- child validation

---

# Phase 03 — Design Token Engine

## Goal

The LLM selects design intent rather than raw CSS values.

Bad:

```json
{
  "padding": 27,
  "radius": 13,
  "fontSize": 31
}
```

Good:

```json
{
  "density": "comfortable",
  "radius": "large",
  "typography": "modern"
}
```

## Token Categories

Implement:

- color
- typography
- spacing
- radius
- shadow
- border
- elevation
- motion
- breakpoint
- container

## Themes

Initial themes:

- modern_light
- modern_dark
- premium_dark
- premium_light
- ecommerce
- SaaS
- editorial
- minimal

## Token Resolution

```text
DesignIntent
    ↓
Theme
    ↓
TokenResolver
    ↓
Concrete implementation values
```

The LLM never needs to generate concrete token values.

Support:

- theme inheritance
- token overrides
- validation
- fallback defaults
- responsive values

## Tests

Test:

- theme lookup
- token resolution
- invalid tokens
- overrides
- defaults
- inheritance

---

# Phase 04 — Layout Grammar

## Objective

Implement a semantic layout grammar so the AI reasons about composition instead of pixel coordinates.

Do NOT make x/y/width/height/absolute positioning the primary layout representation.

## Layout Primitives

Implement:

- container
- stack
- row
- grid
- split
- sidebar
- bento
- centered
- full_bleed
- media_text
- card_grid
- asymmetric_grid

## Semantic Properties

Use:

- density
- gap
- alignment
- distribution
- columns
- ratio
- max_width
- padding

Example:

```json
{
  "type": "split",
  "ratio": "40/60",
  "gap": "xl"
}
```

## Responsive Layout

Support:

- mobile
- tablet
- desktop
- wide

Use semantic responsive rules.

## Validation

Reject:

- impossible nesting
- invalid ratios
- invalid column counts
- unsupported responsive behavior
- overflowing structures

## Deliverables

1. Layout models
2. Layout resolver
3. Responsive resolver
4. Validation
5. Tests

---

# Phase 05 — Design Recipe Engine

## Objective

Provide reusable, high-quality page composition recipes.

Instead of asking the LLM to invent every page structure, provide compositional recipes.

## Initial Recipes

### SaaS Landing

```text
navigation
→ hero
→ social_proof
→ feature_bento
→ product_showcase
→ metrics
→ testimonials
→ pricing
→ faq
→ cta
→ footer
```

### Ecommerce Product

```text
navigation
→ breadcrumb
→ product_detail
→ trust_signals
→ product_features
→ reviews
→ related_products
→ recently_viewed
→ footer
```

### Dashboard

```text
navigation/sidebar
→ page_header
→ stats
→ primary_visualization
→ secondary_content
→ activity
→ footer
```

### Settings

```text
navigation/sidebar
→ page_header
→ settings_navigation
→ settings_sections
→ danger_zone
```

## Recipe Definition

Each recipe defines:

- id
- page_type
- purpose
- sections
- recommended component types
- optional sections
- required sections
- conversion/task goals
- layout rules
- responsive rules

## Customization

The LLM may:

- select recipe
- remove optional sections
- reorder sections where allowed
- select variants
- choose visual direction

The LLM must not arbitrarily destroy required UX hierarchy.

## Deliverables

- RecipeRegistry
- RecipeResolver
- RecipeValidator
- initial production-quality recipes
- tests

---

# Phase 06 — Component and Design Retrieval

## Goal

Never send the entire catalog to the LLM.

Pipeline:

```text
Requirement
→ retrieve relevant design capabilities
→ provide small context
→ LLM generates Design DSL
```

## Metadata

Index:

- component ID
- description
- domain
- capabilities
- layout compatibility
- visual style
- animation capability
- responsive capability

## Retrieval

Use PostgreSQL + pgvector.

Support:

- semantic search
- metadata filtering
- domain filtering
- capability filtering
- style filtering

Example query:

```text
premium SaaS analytics dashboard
```

should retrieve relevant:

- dashboard
- analytics
- statistics
- charts
- premium visual style
- bento layout
- activity components

## Context Budget

Implement a maximum retrieval budget.

Only relevant candidates are sent to the LLM.

## Deliverables

1. Embedding abstraction
2. pgvector repository
3. RetrievalService
4. metadata filtering
5. context builder
6. tests

---

# Phase 07 — Clarifier Agent

## Responsibility

ONLY clarify requirements.

The Clarifier:

- identifies missing information
- asks necessary questions
- detects ambiguity
- provides sensible defaults
- may consult an Advisor when a recommendation is genuinely required

The Clarifier MUST NOT:

- design pages
- create screens
- choose components
- create navigation
- create layouts
- generate UI
- create implementation details

## Output

```json
{
  "status": "ready | needs_clarification",
  "questions": [],
  "assumptions": [],
  "clarified_requirements": {}
}
```

Maximum questions: 3.

Questions must be necessary.

Do not ask questions whose answers can safely use defaults.

Example:

Input:

```text
Build an ecommerce website for shoes.
```

Possible question:

```text
What type of customer should the design primarily target?

- General consumers
- Athletes/runners
- Fashion-focused shoppers
- Premium/luxury shoppers

Default: General consumers
```

## Tests

Verify:

- unnecessary questions are avoided
- maximum 3 questions
- no UI generation
- no screen planning
- no component generation
- no layout generation

---

# Phase 08 — UX Planner Agent

## Responsibility

Transform clarified requirements into a UX-level plan.

The Planner determines:

- user goals
- primary journey
- information architecture
- required screens
- screen purpose
- key content
- required interactions
- (M13) each screen's `route` and `nav_label`, its `links` as `{intent, to}` edges from the intent
  vocabulary, and the `journey` as `{screen, intent, to}` steps that must be among those links

The Planner does NOT determine:

- CSS
- pixel coordinates
- concrete component implementation
- animation implementation

## Output

Example:

```json
{
  "product": "shoe ecommerce",
  "journey": [
    "discover",
    "browse",
    "view",
    "select",
    "cart",
    "checkout"
  ],
  "screens": [
    {
      "id": "home",
      "purpose": "discovery"
    },
    {
      "id": "listing",
      "purpose": "product discovery"
    },
    {
      "id": "detail",
      "purpose": "product evaluation"
    },
    {
      "id": "cart",
      "purpose": "purchase preparation"
    },
    {
      "id": "checkout",
      "purpose": "purchase"
    }
  ]
}
```

Optimize for:

- user flow
- information hierarchy
- task completion
- consistency across screens

Keep output compact.

---

# Phase 09 — Design Director Agent

## Responsibility

Transform the UX plan into a high-level visual design direction.

The Design Director decides:

- visual personality
- design-system direction
- page composition strategy
- appropriate layout recipes
- density
- typography direction
- theme
- visual hierarchy
- animation personality

## Output

```json
{
  "visual_style": "premium_modern",
  "theme": "premium_light",
  "density": "comfortable",
  "typography": "modern_sans",
  "radius": "large",
  "layout_strategy": "editorial_grid",
  "animation": "subtle_expressive",
  "recipe": "ecommerce_product"
}
```

Do not generate:

- CSS
- pixel values
- raw component props
- implementation details
- animation keyframes

## Design Priorities

1. information hierarchy
2. visual balance
3. whitespace
4. content grouping
5. conversion/task flow
6. consistency
7. responsive behavior
8. animation restraint

Keep output extremely compact.

---

# Phase 10 — Compact Design Builder

## Core Principle

Generate a compact semantic Design DSL.

Do NOT generate:

- React
- CSS
- HTML
- Tailwind classes
- Motion code
- implementation details

## Inputs

The Builder receives:

- clarified requirements
- UX plan
- design direction
- retrieved components
- retrieved layouts
- recipe
- relevant learned design lessons

## Output Example

```json
{
  "screen": "product_detail",
  "recipe": "ecommerce_product",
  "sections": [
    {
      "type": "navigation"
    },
    {
      "type": "breadcrumb"
    },
    {
      "type": "product_detail",
      "variant": "premium_split"
    },
    {
      "type": "trust_signals"
    },
    {
      "type": "feature_grid"
    },
    {
      "type": "reviews"
    },
    {
      "type": "related_products"
    }
  ],
  "animation": "subtle_stagger"
}
```

## Responsibilities

Decide:

- section selection
- section ordering
- component selection
- component variants
- layout composition
- content hierarchy
- animation intent

## Must NOT Decide

- CSS
- exact spacing values
- exact colors
- implementation component names
- animation keyframes
- DOM structure
- React code

## Token Optimization

Prefer:

```json
{
  "type": "product_grid",
  "variant": "premium"
}
```

over fully expanded configuration.

Use defaults aggressively.

Never repeat default values.

## Validation

Validate against:

- ComponentRegistry
- RecipeRegistry
- LayoutRegistry
- TokenRegistry
- AnimationRegistry

Unknown IDs must be impossible through structured schemas or rejected before rendering.

---

# Phase 11 — Deterministic Design Resolver

## Objective

Convert semantic Design DSL into a fully resolved UI representation without an LLM.

Pipeline:

```text
DesignDSL
→ recipe expansion
→ component resolution
→ variant resolution
→ layout resolution
→ token resolution
→ responsive resolution
→ animation resolution
→ RenderModel
```

## Requirements

The resolver must:

- validate every ID
- resolve defaults
- expand recipes
- resolve component implementations
- resolve layout primitives
- resolve tokens
- resolve responsive behavior
- resolve animations

The LLM must not be called during deterministic resolution.

## RenderModel

Create a strongly typed RenderModel containing enough information for rendering:

- concrete component implementation
- props
- CSS token references
- layout configuration
- responsive rules
- animation configuration

The LLM must not produce this model directly.

## Tests

Test:

```text
DesignDSL → RenderModel
```

including invalid input.

---

# Phase 12 — Animation Engine

## Goal

Provide impressive animation without requiring the LLM to generate animation implementation.

## Animation Vocabulary

Initial animations:

- fade
- fade_up
- fade_down
- scale
- reveal
- stagger
- slide
- parallax
- float
- glow
- marquee
- magnetic
- morph
- number_ticker

## Intensity

Support:

- none
- subtle
- moderate
- expressive

## Semantic API

Example:

```json
{
  "animation": "stagger",
  "intensity": "subtle"
}
```

Resolve this into concrete animation configuration.

## Engine

Create:

```python
class AnimationEngine(Protocol):
    ...
```

Initial implementation:

```text
MotionAnimationEngine
```

Allow future:

```text
GSAPAnimationEngine
```

## Important

The LLM should not generate:

- duration
- easing arrays
- keyframes
- raw Motion code

unless an explicit advanced extension requires it.

## Accessibility

Support reduced motion.

When reduced motion is enabled:

- disable unnecessary movement
- preserve information
- preserve state transitions

## Deliverables

- AnimationRegistry
- AnimationResolver
- Motion adapter
- reduced-motion support
- tests

---

# Phase 13 — Renderer

## Architecture

```text
RenderModel
→ Component Resolver
→ React representation
→ Browser
→ Screenshot
```

The renderer must be deterministic.

## Requirements

Support:

- component rendering
- nested layouts
- responsive behavior
- themes
- animations
- content
- accessibility
- error boundaries

## Component Mapping

Example:

```text
product_card
    ↓
Card
Image
Badge
Price
Button
Motion
```

Mappings must live in the component catalog.

Do not put mappings inside agents.

## Output

```json
{
  "html": "...",
  "url": "...",
  "screenshot": "...",
  "render_time_ms": 123
}
```

Rendering failures must produce structured errors.

Do not silently hide errors with fallback UI.

---

# Phase 14 — Screenshot UI/UX Verifier

## Evidence Priority

1. Screenshot
2. Deterministic findings
3. DOM/outline
4. Design requirements
5. UX plan

Screenshot-visible issues are primary.

## Verify

### Layout

- alignment
- spacing
- hierarchy
- balance
- overflow
- clipping
- responsive issues

### Visual

- contrast
- typography
- consistency
- density
- hierarchy

### UX

- missing actions
- unclear states
- confusing hierarchy
- accessibility problems

### Responsive

Check:

- mobile
- tablet
- desktop

## Deterministic Findings

Existing deterministic checks are authoritative for:

- overflow
- invalid geometry
- contrast failure
- missing required section
- target-size failure

## Output

```json
{
  "status": "pass | needs_fix",
  "issues": [
    {
      "severity": "critical | major | minor",
      "dimension": "layout | visual | ux | accessibility",
      "target": "component_id",
      "issue": "...",
      "suggestion": "..."
    }
  ]
}
```

Do not:

- report invisible implementation issues
- invent problems
- rewrite the entire screen

Return actionable findings only.

---

# Phase 15 — Targeted Fixer

## Goal

Apply the smallest changes necessary to resolve verifier findings.

Do NOT regenerate the entire page.

Example:

```json
{
  "target": "hero_01",
  "change": {
    "property": "layout",
    "value": "split"
  }
}
```

Another example:

```json
{
  "target": "product_grid_01",
  "change": {
    "property": "columns",
    "value": "3"
  }
}
```

## Fix Priority

1. Critical layout problems
2. Missing required content
3. Accessibility
4. Responsive issues
5. Visual hierarchy
6. Minor polish

## Guardrails

The Fixer must:

- use known component IDs
- use known token IDs
- use known layout values
- never invent IDs
- never modify unrelated sections

## Iteration Limit

Make maximum iterations configurable.

Example:

```python
MAX_DESIGN_ITERATIONS = 3
```

Never allow an infinite verifier/fixer loop.

---

# Phase 16 — Learning System

## Goal

Learn reusable design rules from successful verified fixes.

Example:

Repeated observation:

```text
Product grids fail because cards become too narrow.
```

Verified fix:

```text
Reduce columns from 4 to 3.
```

Potential lesson:

```text
For desktop product grids with long product titles,
prefer 3 columns when the container is below the wide breakpoint.
```

## Lifecycle

```text
candidate
→ validated
→ trusted
```

Require repeated successful confirmation before a lesson becomes trusted.

## Store

Use PostgreSQL + pgvector.

Store:

- lesson
- embedding
- scope
- evidence
- confirmations
- violations
- status

## Retrieval

Retrieve lessons based on:

- domain
- page type
- component
- layout
- problem type

## Guardrails

Prevent:

- tenant-specific data leakage
- user-specific strings
- secrets
- transient values
- unverified advice

Unverified lessons must never directly override deterministic design rules.

---

# Phase 17 — Complete LangGraph Orchestration

## Workflow

```text
START
 ↓
Clarifier
 ↓
Planner
 ↓
Design Director
 ↓
Component/Layout Retrieval
 ↓
Design Builder
 ↓
Deterministic Resolver
 ↓
Renderer
 ↓
Verifier
 ↓
Fixer
 ↓
Renderer
 ↓
Verifier
 ↓
Finalize
```

Learning retrieval can occur before Design Builder.

## Conditional Routing

Clarifier:

```text
needs_clarification → Ask User
ready → Planner
```

Verifier:

```text
pass → Finalize
needs_fix → Fixer
```

Fixer:

```text
success → Renderer
failure → controlled error
```

## Maximum Iterations

Make iteration count configurable.

Never permit an infinite loop.

## Persistence

Persist:

- requirement
- clarification
- plan
- design direction
- design DSL
- render model
- verification
- fixes
- iteration count

Use LangGraph checkpointing where appropriate.

## Cost Optimization

LLM calls should primarily happen for:

1. Clarification
2. Planning
3. Design direction
4. Design DSL generation
5. Screenshot verification
6. Complex fixing when deterministic fixing is insufficient

Do NOT use an LLM for:

- component resolution
- token resolution
- layout calculation
- animation implementation
- validation
- recipe expansion
- rendering

## Token Optimization

Never send:

- complete component catalog
- complete token catalog
- complete animation implementation
- raw React code
- previous giant JSON documents

Use:

- retrieval
- compact context
- IDs
- defaults
- semantic DSL
- structured outputs

## Observability

Track:

- input tokens
- output tokens
- latency
- model
- LLM calls
- retrieval count
- rendering time
- verifier iterations
- fixes
- final quality

## Final Acceptance Criteria

A generated screen should:

- satisfy requirements
- have clear information hierarchy
- use appropriate composition
- use registered components only
- use valid design tokens
- be responsive
- have coherent animation
- pass deterministic validation
- pass screenshot verification

---

# Central Design DSL

The Design DSL is the central contract between the LLM and deterministic engine.

Recommended shape:

```python
class DesignSpec(BaseModel):
    screen_id: str
    recipe: str
    visual_style: str
    theme: str
    density: str
    sections: list[SectionSpec]
    animation: AnimationIntent | None = None


class SectionSpec(BaseModel):
    id: str
    type: str
    variant: str | None = None
    layout: LayoutIntent | None = None
    children: list["SectionSpec"] = []
    content: dict[str, str] = {}
```

Example:

```json
{
  "screen_id": "product_detail",
  "recipe": "ecommerce_product",
  "visual_style": "premium_modern",
  "theme": "premium_light",
  "density": "comfortable",
  "sections": [
    {
      "id": "navigation",
      "type": "navigation"
    },
    {
      "id": "product",
      "type": "product_detail",
      "variant": "premium_split"
    },
    {
      "id": "reviews",
      "type": "reviews"
    },
    {
      "id": "related",
      "type": "related_products"
    }
  ],
  "animation": {
    "name": "subtle_stagger",
    "intensity": "subtle"
  }
}
```

The LLM output should normally remain small.

The deterministic system can expand it into a much larger RenderModel.

---

# Recommended Component Library Strategy

Use a layered frontend component system:

```text
Semantic Component Catalog
        ↓
┌──────────────────────────────┐
│ shadcn/ui                    │
│ Radix                        │
│ Magic UI                     │
│ Aceternity UI                │
│ React Bits                   │
└──────────────┬───────────────┘
               ↓
        Motion Animation
               ↓
        Optional GSAP
```

The LLM should select semantic components rather than library implementation names.

Example:

```text
hero_aurora
```

can map internally to:

```text
Aceternity
+
Motion
+
your design tokens
```

while:

```text
product_card
```

can map to:

```text
shadcn Card
+
Image
+
Badge
+
Button
+
Motion
```

This allows the library stack to evolve without changing the agent contracts.

---

# Final Architecture Principle

The system should maintain a strict separation:

## LLM

Responsible for:

- WHAT
- WHY
- hierarchy
- composition
- visual direction
- component selection
- variant selection
- animation intent

## Deterministic Engine

Responsible for:

- HOW
- CSS
- exact spacing
- exact colors
- grid calculations
- responsive implementation
- component implementation
- animation implementation
- accessibility rules
- validation
- rendering

The most important optimization is therefore:

```text
Do not optimize a 2,000-line generated JSON.

Remove the reason the LLM needs to generate 2,000 lines.
```

Target:

```text
Requirement
→ compact design decisions
→ ~200–500 token Design DSL
→ deterministic expansion
→ thousands of implementation details
```

This gives the system lower generation cost, lower failure rate, better schema safety, and greater freedom to build sophisticated UIs.
