"""DesignSpec -> RenderModel. Fully deterministic; this package may not import the LLM layer."""

from __future__ import annotations

from dataclasses import dataclass

from app.animation import AnimationResolver
from app.catalog import ComponentDefinition, ComponentRegistry
from app.core.exceptions import ResolutionError, ValidationError
from app.dsl.choreography import allowed_motion, choreograph
from app.layout import LayoutResolver, LayoutSpec, LayoutType
from app.models.common import Breakpoint, Density, Intensity
from app.models.dsl import AnimationIntent, DesignSpec, LayoutIntent, SectionSpec
from app.models.render import MotionBehavior, RenderModel, RenderNode, ResolvedLayout
from app.recipes import RecipeResolver
from app.tokens import TokenResolver
from app.tokens.resolver import ResolvedTokens

# Design-direction words the LLM may use, mapped to a page-level animation vocabulary entry.
PAGE_ANIMATION_ALIASES: dict[str, tuple[str, Intensity]] = {
    "subtle_stagger": ("stagger", Intensity.subtle),
    "subtle_expressive": ("fade_up", Intensity.moderate),
    "subtle": ("fade_up", Intensity.subtle),
    "expressive": ("fade_up", Intensity.expressive),
    "none": ("none", Intensity.none),
}


@dataclass
class ResolverContext:
    reduced_motion: bool = False
    page_animation: AnimationIntent | None = None


class DesignResolver:
    def __init__(
        self,
        components: ComponentRegistry,
        tokens: TokenResolver,
        layouts: LayoutResolver,
        recipes: RecipeResolver,
        animations: AnimationResolver,
    ) -> None:
        self._components = components
        self._tokens = tokens
        self._layouts = layouts
        self._recipes = recipes
        self._animations = animations

    # ---------------------------------------------------------------------------------------
    def resolve(self, spec: DesignSpec, *, reduced_motion: bool = False) -> RenderModel:
        try:
            return self._resolve(spec, reduced_motion)
        except ValidationError:
            raise
        except Exception as e:  # noqa: BLE001 - convert to a structured, non-silent failure
            raise ResolutionError(f"resolution failed for {spec.screen_id}: {e}") from e

    def _resolve(self, spec: DesignSpec, reduced_motion: bool) -> RenderModel:
        spec = self._recipes.resolve(spec)  # recipe expansion + defaults + hierarchy validation
        recipe = self._recipes._validator._recipes.get(spec.recipe)
        tokens = self._tokens.resolve(
            spec.theme,
            density=spec.density,
            palette=spec.palette,
            typography=spec.typography,
            radius=spec.radius,
        )
        ctx = ResolverContext(
            reduced_motion=reduced_motion, page_animation=self._page_animation(spec.animation)
        )

        children = self._compose_shell(recipe.shell, spec.sections, ctx)
        page_intensity = ctx.page_animation.intensity if ctx.page_animation else Intensity.subtle
        shell = self._layouts.resolve(
            LayoutSpec(type=recipe.shell, gap="none", padding="none", max_width="full"),
            child_count=len(children),
        )
        root = RenderNode(
            id="page",
            semantic_type="page",
            implementation="Page",
            layout=shell,
            children=children,
            props={
                "recipe": recipe.id,
                "visual_style": spec.visual_style,
                "density": str(spec.density),
            },
        )
        choreograph(root, page_intensity, self._animations)
        return self._model(spec.screen_id, spec.theme, tokens, root, reduced_motion)

    def preview(
        self,
        sections: list[SectionSpec],
        *,
        screen_id: str = "preview",
        theme: str = "modern_light",
        palette: str | None = None,
        typography: str | None = None,
        radius: str | None = None,
        density: Density = Density.comfortable,
        intensity: Intensity = Intensity.moderate,
    ) -> RenderModel:
        """Render sections without a recipe: the component gallery and visual review use this.
        Components, variants, slots and tokens are validated exactly as in a real page."""
        tokens = self._tokens.resolve(
            theme, density=density, palette=palette, typography=typography, radius=radius
        )
        ctx = ResolverContext()
        children = [self._resolve_section(s, ctx, parent_layout=LayoutType.stack) for s in sections]
        root = RenderNode(
            id="page",
            semantic_type="page",
            implementation="Page",
            layout=self._layouts.resolve(
                LayoutSpec(type=LayoutType.stack, gap="none", padding="none", max_width="full"),
                child_count=len(children),
            ),
            children=children,
        )
        choreograph(root, intensity, self._animations)
        return self._model(screen_id, theme, tokens, root, reduced_motion=False)

    @staticmethod
    def _model(
        screen_id: str, theme: str, tokens: ResolvedTokens, root: RenderNode, reduced_motion: bool
    ) -> RenderModel:
        css = tokens.css_variables()
        for bp in Breakpoint:
            for k, v in tokens.css_variables_for(bp).items():
                css[f"{k}@{bp.value}"] = v
        return RenderModel(
            screen_id=screen_id,
            theme=theme,
            css_variables=css,
            root=root,
            reduced_motion=reduced_motion,
        )

    def _compose_shell(
        self, shell: LayoutType, sections: list[SectionSpec], ctx: ResolverContext
    ) -> list[RenderNode]:
        """Two-pane shells get [nav pane, main stack]; everything else is a flat stack."""
        if shell in (LayoutType.sidebar, LayoutType.split_) and len(sections) > 2:
            nav_idx = next(
                (
                    i
                    for i, s in enumerate(sections)
                    if self._components.get(s.type).category == "navigation"
                    and "app_shell" in self._components.get(s.type).capabilities
                ),
                0,
            )
            nav = self._resolve_section(sections[nav_idx], ctx, parent_layout=shell)
            rest = [s for i, s in enumerate(sections) if i != nav_idx]
            main_children = [
                self._resolve_section(s, ctx, parent_layout=LayoutType.stack) for s in rest
            ]
            main_layout = self._layouts.resolve(
                LayoutSpec(type=LayoutType.stack, gap="lg", padding="lg"),
                child_count=len(main_children),
                parent=shell,
            )
            main = RenderNode(
                id="main",
                semantic_type="main",
                implementation="Main",
                layout=main_layout,
                children=main_children,
            )
            return [nav, main]
        return [self._resolve_section(s, ctx, parent_layout=shell) for s in sections]

    # ---------------------------------------------------------------------------------------
    def _resolve_section(
        self, s: SectionSpec, ctx: ResolverContext, *, parent_layout: LayoutType | None
    ) -> RenderNode:
        comp = self._components.get(s.type)
        variant = self._components.validate_variant(comp.id, s.variant)
        if s.content:
            self._components.validate_slots(comp.id, set(s.content))
        for child in s.children:
            self._components.validate_child(comp.id, child.type)

        layout = self._resolve_layout(
            comp, s.layout, child_count=len(s.children), parent=parent_layout
        )
        layout_type = LayoutType(layout.type) if layout else None
        children = [self._resolve_section(c, ctx, parent_layout=layout_type) for c in s.children]

        animation = None
        motion: list[MotionBehavior] = []
        explicit = s.animation
        if (
            explicit is not None
            and self._animations.definition(explicit.name).category != "entrance"
        ):
            # A behaviour (parallax, count-up, magnetic...) rather than an entrance: validated
            # against the component, run by the motion runtime, and the section still enters
            # with the page default.
            self._animations.resolve(explicit, allowed=allowed_motion(comp))
            if (b := self._animations.behavior(explicit)) is not None:
                motion.append(b)
            explicit = None
        if explicit is not None:  # explicit entrance: must be supported
            animation = self._animations.resolve(
                explicit, child_count=max(len(children), 1), allowed=allowed_motion(comp)
            )
        elif ctx.page_animation is not None:  # page default: degrade to what the component supports
            intent = ctx.page_animation
            if intent.name not in comp.animation_capabilities and intent.name != "none":
                fallback = next(
                    (a for a in ("fade_up", "fade", "none") if a in comp.animation_capabilities),
                    "none",
                )
                intent = AnimationIntent(name=fallback, intensity=intent.intensity)
            animation = self._animations.resolve(intent, child_count=max(len(children), 1))
        props: dict[str, object] = {**comp.implementation.default_props, "variant": variant}
        props.update(s.content)
        props["parts"] = [p.name for p in comp.implementation.parts]
        return RenderNode(
            id=s.id,
            semantic_type=comp.id,
            implementation=comp.implementation.root,
            props=props,
            tokens=self._component_tokens(comp),
            layout=layout,
            animation=animation,
            motion=motion,
            children=children,
        )

    def _resolve_layout(
        self,
        comp: ComponentDefinition,
        intent: LayoutIntent | None,
        *,
        child_count: int,
        parent: LayoutType | None,
    ) -> ResolvedLayout | None:
        if intent is None:
            return None
        if comp.supported_layouts and intent.type not in comp.supported_layouts:
            raise ValidationError(
                f"{comp.id} does not support layout '{intent.type}'; "
                f"allowed: {comp.supported_layouts}",
                target=comp.id,
            )
        spec = LayoutSpec(
            type=intent.type,
            **{k: v for k, v in intent.model_dump(exclude={"type"}).items() if v is not None},
        )
        # component responsive hints (e.g. product_grid columns per breakpoint) become overrides
        for bp, rules in comp.responsive_behavior.rules.items():
            cols = rules.get("columns")
            if (
                isinstance(cols, int)
                and bp not in spec.responsive
                and self._layouts._reg.get(spec.type.value).supports_columns
            ):
                spec.responsive[bp] = spec.responsive.get(bp) or LayoutOverride(columns=cols)
        # the layout wraps this component's children when it has them; a leaf component's internal
        # layout (e.g. hero split) uses the primitive's own minimum pane count.
        ldef = self._layouts._reg.get(spec.type.value)
        n = child_count if child_count else max(ldef.min_children, 1)
        return self._layouts.resolve(spec, child_count=n, parent=parent)

    @staticmethod
    def _component_tokens(comp: ComponentDefinition) -> dict[str, str]:
        base = {
            "bg": "var(--color-bg)",
            "fg": "var(--color-fg)",
            "radius": "var(--radius-base)",
            "font_heading": "var(--typography-font-heading)",
            "font_body": "var(--typography-font-body)",
            "section_padding": "var(--spacing-section)",
        }
        if comp.design_metadata.conversion_role == "primary_cta":
            base["accent"] = "var(--color-primary)"
            base["accent_fg"] = "var(--color-primary-fg)"
        if comp.category in ("commerce", "data"):
            base["surface"] = "var(--color-surface)"
            base["border"] = "var(--color-border)"
            base["shadow"] = "var(--shadow-md)"
        return base

    @staticmethod
    def _page_animation(intent: AnimationIntent | None) -> AnimationIntent | None:
        if intent is None:
            return None
        alias = PAGE_ANIMATION_ALIASES.get(intent.name)
        if alias is None:
            return intent
        name, default_intensity = alias
        intensity = intent.intensity if intent.intensity != Intensity.subtle else default_intensity
        return AnimationIntent(name=name, intensity=intensity)


from app.layout.models import LayoutOverride  # noqa: E402  (kept at bottom to avoid cycle noise)
