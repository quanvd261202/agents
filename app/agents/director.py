"""Phase 09 - Design Director. Chooses the visual direction, never the pixels."""

from __future__ import annotations

from app.agents.base import Agent, brief_block
from app.animation.registry import AnimationRegistry
from app.core.exceptions import ValidationError
from app.core.llm import LLMProvider
from app.dsl.resolver import PAGE_ANIMATION_ALIASES
from app.models.direction import DesignDirection
from app.models.plan import UXPlan
from app.models.requirements import ClarifiedRequirements
from app.recipes.registry import RecipeRegistry
from app.tokens.palettes import PaletteRegistry, default_palette_registry
from app.tokens.registry import ThemeRegistry

SYSTEM = """You are a design director. You set the visual direction for a product, at the level a
design lead would brief: personality, theme, density, typography, rhythm, motion.

You MUST NOT produce: CSS, pixel values, hex colors, component props, class names, DOM structure,
or animation keyframes. A deterministic engine expands your direction into all of that.

Priorities, in order: information hierarchy, visual balance, whitespace, content grouping,
task/conversion flow, consistency, responsive behaviour, animation restraint.

The direction is shared by every screen so the product stays consistent. `screens` assigns each
planned screen, exactly once, the recipe whose page type fits that screen's purpose.

Pick `theme`, `palette`, `typography`, `radius`, every screen's `recipe` and `animation` from the
allowed values only. The palette is the brand's colour system and overrides the theme's colours:
match its mood to the brand. Typography sets the voice; radius sets the corner personality (none =
sharp and editorial, large = soft and friendly, full = pill buttons). `animation` sets the page's
motion intensity, which a deterministic choreographer expands per section: none = still;
subtle / subtle_stagger = quiet (items fade in, cards lift, numbers count up); subtle_expressive =
moderate (plus headline reveals, imagery settling as it scrolls, a magnetic primary CTA);
expressive = parallax, stacking sections and ambient light. Match it to the brand: restraint reads
premium, and a busy page reads cheap. `visual_style` and
`layout_strategy` are short snake_case words (e.g. premium_modern, editorial_grid). Keep the whole
output extremely compact.

When the user's brief describes a brand or visual direction, it decides the personality, theme,
density and motion; do not fall back to a generic look it rules out."""

USER = """Product: {product} ({domain})
Audience: {audience}
Primary goal: {goal}
Journey: {journey}
Screens: {screens}

Allowed themes: {themes}
Allowed palettes (id - mood):
{palettes}
Allowed typography (id - mood):
{typography}
Allowed radius: {radii}
Allowed animation: {animations}
Allowed recipes:
{recipes}{brief}"""


class DirectorAgent(Agent):
    """Satisfies app.services.interfaces.DesignDirectorService."""

    name = "director"

    def __init__(
        self,
        llm: LLMProvider,
        themes: ThemeRegistry,
        recipes: RecipeRegistry,
        animations: AnimationRegistry,
        palettes: PaletteRegistry | None = None,
    ) -> None:
        super().__init__(llm)
        self._themes = themes
        self._recipes = recipes
        self._animations = animations
        self._palettes = palettes or default_palette_registry()

    def _typography(self) -> dict[str, dict[str, str]]:
        return self._themes.get("base").typography_presets

    def _radii(self) -> list[str]:
        return list(self._themes.get("base").radius_scale)

    def _animation_names(self) -> list[str]:
        return [*PAGE_ANIMATION_ALIASES, *self._animations.ids()]

    async def direct(
        self, req: ClarifiedRequirements, plan: UXPlan, brief: str = ""
    ) -> DesignDirection:
        recipes = self._recipes.for_domain(req.domain)
        allowed_recipes = [r.id for r in recipes]
        return await self._invoke(
            SYSTEM,
            USER.format(
                product=req.product,
                domain=req.domain,
                audience=req.target_audience,
                goal=req.primary_goal,
                journey=" -> ".join(plan.journey),
                screens=", ".join(f"{s.id} ({s.purpose})" for s in plan.screens),
                themes=", ".join(t for t in self._themes.ids() if t != "base"),
                recipes="\n".join(f"- {r.id} ({r.page_type}): {r.purpose}" for r in recipes),
                animations=", ".join(self._animation_names()),
                palettes="\n".join(
                    f"- {p.id} ({p.mode}) - {', '.join(p.mood)}" for p in self._palettes
                ),
                typography="\n".join(
                    f"- {k} - {v.get('mood', '')}" for k, v in self._typography().items()
                ),
                radii=", ".join(self._radii()),
                brief=brief_block(brief),
            ),
            DesignDirection,
            lambda d: self._validate(d, plan, allowed_recipes),
        )

    def _validate(
        self, d: DesignDirection, plan: UXPlan, allowed_recipes: list[str]
    ) -> DesignDirection:
        planned = [s.id for s in plan.screens]
        assigned = [s.screen_id for s in d.screens]
        if sorted(assigned) != sorted(planned):
            raise ValidationError(
                f"`screens` must assign each of {planned} exactly once; got {assigned}",
                target="screens",
            )
        for s in d.screens:
            if s.recipe not in allowed_recipes:
                raise ValidationError(
                    f"recipe '{s.recipe}' for screen '{s.screen_id}'; allowed: {allowed_recipes}",
                    target=s.screen_id,
                )
        if not self._themes.exists(d.theme) or d.theme == "base":
            raise ValidationError(f"unknown theme '{d.theme}'", target="theme")
        if d.palette is not None and not self._palettes.exists(d.palette):
            raise ValidationError(
                f"unknown palette '{d.palette}'; allowed: {self._palettes.ids()}", target="palette"
            )
        if d.typography not in self._typography():
            raise ValidationError(
                f"unknown typography '{d.typography}'; allowed: {list(self._typography())}",
                target="typography",
            )
        if d.radius not in self._radii():
            raise ValidationError(
                f"unknown radius '{d.radius}'; allowed: {self._radii()}", target="radius"
            )
        if d.animation not in self._animation_names():
            raise ValidationError(f"unknown animation '{d.animation}'", target="animation")
        return d
