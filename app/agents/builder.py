"""Phase 10 - Compact Design Builder. Emits the semantic Design DSL and nothing lower."""

from __future__ import annotations

from pydantic import Field

from app.agents.base import Agent
from app.animation.registry import AnimationRegistry
from app.catalog.registry import ComponentRegistry
from app.core.exceptions import ValidationError
from app.core.llm import LLMProvider
from app.core.logging import get_logger
from app.dsl.choreography import allowed_motion
from app.dsl.resolver import PAGE_ANIMATION_ALIASES
from app.models.common import Intensity, StrictModel
from app.models.direction import DesignDirection
from app.models.dsl import AnimationIntent, DesignSpec, SectionSpec
from app.models.plan import ScreenPlan
from app.models.requirements import ClarifiedRequirements
from app.recipes.models import RecipeDefinition
from app.recipes.registry import RecipeRegistry
from app.recipes.resolver import RecipeValidator
from app.retrieval.models import RetrievedContext

log = get_logger(__name__)

SYSTEM = """You compose one screen as a compact semantic Design DSL.

You MUST NOT produce: React, HTML, CSS, Tailwind classes, Motion code, hex colors, spacing values,
implementation component names, or DOM structure. A deterministic engine expands your output.

You decide only: which of the recipe's sections appear, their order, each section's component type
and variant, and each section's animation intent.

Rules:
- `id` must be a section slot of the recipe below. Never invent one, never repeat one.
- `type` must be one of that slot's allowed component types.
- `variant` must be one the component offers; omit it to take the recipe default.
- Every required slot must appear.
- Fixed slots keep the recipe's order. Only slots marked `reorderable` may move, and only within
  their own group.
- `animation` is per-section only, and only from that component's `motion` list. The page-level
  motion strategy is already set by the design direction below; omit `animation` unless a section
  genuinely needs to differ from it.
- Include an optional slot only when the product needs it. A shorter, sharper page beats a long one.

Use defaults aggressively and never restate a default."""

USER = """Screen: {screen_id} - {purpose}
Key content: {content}
Interactions: {interactions}

Product: {product} ({domain}), for {audience}. Goal: {goal}
Visual direction: {style}, density {density}, layout strategy {strategy}, animation {animation}

Recipe `{recipe}` - {recipe_purpose}
Section slots (in recipe order):
{slots}

Retrieved components:
{components}

Retrieved layouts:
{layouts}
{lessons}"""


class BuilderSection(StrictModel):
    """One chosen section. Deliberately narrower than SectionSpec: the rest is derived."""

    id: str
    type: str
    variant: str | None = None
    animation: str | None = None


class BuilderOutput(StrictModel):
    """Only what the builder owns. `screen_id`, recipe, theme, style, density and the page-level
    animation are derived from upstream state, so drift into them is not representable."""

    sections: list[BuilderSection] = Field(min_length=1)


class DesignBuilderAgent(Agent):
    """Satisfies app.services.interfaces.DesignBuilderService."""

    name = "builder"

    def __init__(
        self,
        llm: LLMProvider,
        recipes: RecipeRegistry,
        components: ComponentRegistry,
        animations: AnimationRegistry,
    ) -> None:
        super().__init__(llm)
        self._recipes = recipes
        self._components = components
        self._animations = animations
        self._validator = RecipeValidator(recipes, components)

    async def build(
        self,
        req: ClarifiedRequirements,
        screen: ScreenPlan,
        direction: DesignDirection,
        context: RetrievedContext,
    ) -> DesignSpec:
        recipe = self._recipes.get(direction.recipe_for(screen.id))
        user = USER.format(
            screen_id=screen.id,
            purpose=screen.purpose,
            content=", ".join(screen.key_content) or "(not specified)",
            interactions=", ".join(screen.interactions) or "(not specified)",
            product=req.product,
            domain=req.domain,
            audience=req.target_audience,
            goal=req.primary_goal,
            style=direction.visual_style,
            density=direction.density.value,
            strategy=direction.layout_strategy,
            animation=direction.animation,
            recipe=recipe.id,
            recipe_purpose=recipe.purpose,
            slots=self._slot_table(recipe),
            components="\n".join(context.components) or "(none)",
            layouts="\n".join(context.layouts) or "(none)",
            lessons=("\nLessons learned:\n" + "\n".join(context.lessons))
            if context.lessons
            else "",
        )
        out = await self._invoke(
            SYSTEM,
            user,
            BuilderOutput,
            lambda o: self._validate(o, screen.id, direction),
        )
        return self._assemble(out, screen.id, direction)

    def _slot_table(self, recipe: RecipeDefinition) -> str:
        lines = []
        for s in recipe.sections:
            types = " | ".join(self._component_line(t) for t in s.component_types)
            flags = "required" if s.required else "optional"
            if s.reorderable:
                flags += f", reorderable in group '{s.reorder_group}'"
            lines.append(f"- {s.id}: {types} [{flags}] - {s.purpose}")
        return "\n".join(lines)

    def _component_line(self, type_id: str) -> str:
        comp = self._components.get(type_id)
        return (
            f"{comp.id}(variants: {', '.join(comp.variants)}"
            f"; motion: {', '.join(allowed_motion(comp))})"
        )

    # -------------------------------------------------------------------------------------
    def _validate(
        self, out: BuilderOutput, screen_id: str, direction: DesignDirection
    ) -> BuilderOutput:
        out = self._fill_fixed_slots(out, self._recipes.get(direction.recipe_for(screen_id)))
        sections = list(out.sections)
        for i, s in enumerate(sections):
            if s.animation is None:
                continue
            if not self._animations.exists(s.animation):
                raise ValidationError(f"unknown animation '{s.animation}'", target=s.id)
            # The resolver rejects motion a component does not support; catch it while the
            # model can still be asked to fix it.
            if not self._components.exists(s.type):
                continue  # the recipe validator below owns the unknown-type message
            allowed = allowed_motion(self._components.get(s.type))
            if s.animation in allowed:
                continue
            fallback = self._entrance_fallback(s.animation, allowed)
            if fallback is None:
                raise ValidationError(
                    f"'{s.type}' does not support animation '{s.animation}'; allowed: {allowed}",
                    target=s.id,
                )
            # An entrance is an intent, not a behaviour: like the resolver does for the page
            # default, degrade it to what the component can do instead of a repair round trip.
            log.info("builder.animation_degraded", section=s.id, wanted=s.animation, got=fallback)
            sections[i] = s.model_copy(update={"animation": fallback})
        if sections != out.sections:
            out = BuilderOutput(sections=sections)
        # The recipe validator owns slot membership, component types, variants and ordering.
        self._validator.validate(self._assemble(out, screen_id, direction))
        return out

    def _entrance_fallback(self, animation: str, allowed: list[str]) -> str | None:
        if self._animations.get(animation).category != "entrance":
            return None
        return next((a for a in ("fade_up", "fade", "stagger", "none") if a in allowed), None)

    @staticmethod
    def _fill_fixed_slots(out: BuilderOutput, recipe: RecipeDefinition) -> BuilderOutput:
        """A required slot with a single allowed component leaves nothing to decide, so a model
        that omits it (usually the footer) is completed here instead of sent back to repair."""
        order = {s.id: i for i, s in enumerate(recipe.sections)}
        sections = list(out.sections)
        present = {s.id for s in sections}
        for slot in recipe.sections:
            if slot.required and len(slot.component_types) == 1 and slot.id not in present:
                at = next(
                    (i for i, s in enumerate(sections) if order.get(s.id, -1) > order[slot.id]),
                    len(sections),
                )
                sections.insert(at, BuilderSection(id=slot.id, type=slot.component_types[0]))
        return out if len(sections) == len(out.sections) else BuilderOutput(sections=sections)

    def _assemble(
        self, out: BuilderOutput, screen_id: str, direction: DesignDirection
    ) -> DesignSpec:
        intensity = _page_intensity(direction.animation)
        return DesignSpec(
            screen_id=screen_id,
            recipe=direction.recipe_for(screen_id),
            visual_style=direction.visual_style,
            theme=direction.theme,
            density=direction.density,
            palette=direction.palette,
            typography=direction.typography,
            radius=direction.radius,
            sections=[
                SectionSpec(
                    id=s.id,
                    type=s.type,
                    variant=s.variant,
                    animation=AnimationIntent(name=s.animation, intensity=intensity)
                    if s.animation
                    else None,
                )
                for s in out.sections
            ],
            animation=AnimationIntent(name=direction.animation, intensity=intensity),
        )


def _page_intensity(direction_animation: str) -> Intensity:
    """Intensity of the page-level motion the director asked for. PAGE_ANIMATION_ALIASES is the
    single source of truth: the resolver reads the same table when it expands the intent."""
    alias = PAGE_ANIMATION_ALIASES.get(direction_animation)
    return alias[1] if alias else Intensity.subtle
