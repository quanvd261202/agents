from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from app.models.common import Breakpoint, StrictModel


class ComponentCategory(StrEnum):
    navigation = "navigation"
    marketing = "marketing"
    commerce = "commerce"
    data = "data"
    forms = "forms"
    content = "content"
    feedback = "feedback"
    structure = "structure"


class SlotDefinition(StrictModel):
    name: str
    required: bool = False
    description: str = ""


class ImplementationPart(StrictModel):
    """One frontend primitive used to implement a semantic component."""

    name: str  # e.g. "Card", "Image", "Badge"
    library: str = "shadcn"  # shadcn | radix | magicui | aceternity | reactbits | motion | native
    role: str = ""


class ImplementationMapping(StrictModel):
    root: str  # React component name the renderer dispatches on
    parts: list[ImplementationPart] = Field(default_factory=list)
    default_props: dict[str, str | int | bool] = Field(default_factory=dict)


class ResponsiveBehavior(StrictModel):
    """Per-breakpoint semantic hints (e.g. columns collapse)."""

    rules: dict[Breakpoint, dict[str, str | int]] = Field(default_factory=dict)


class DesignMetadata(StrictModel):
    visual_styles: list[str] = Field(default_factory=list)  # premium, minimal, playful...
    density_support: list[str] = Field(
        default_factory=lambda: ["compact", "comfortable", "spacious"]
    )
    conversion_role: str | None = None  # e.g. "primary_cta", "trust"


class ComponentDefinition(StrictModel):
    id: str
    category: ComponentCategory
    description: str
    capabilities: list[str] = Field(default_factory=list)
    supported_domains: list[str] = Field(default_factory=lambda: ["*"])
    supported_layouts: list[str] = Field(default_factory=list)
    variants: list[str] = Field(default_factory=lambda: ["standard"])
    default_variant: str = "standard"
    slots: list[SlotDefinition] = Field(default_factory=list)
    allowed_children: list[str] = Field(default_factory=list)  # semantic ids; empty = leaf
    #: Content-model item field -> slot, for a component that shows one item (a card, a buy
    #: box). Non-empty means the Copywriter binds the section to an item and these slots take
    #: the item's values, so every screen agrees on names and prices.
    binds: dict[str, str] = Field(default_factory=dict)
    #: Role -> intents it can carry, in order of preference. The resolver gives the role the href
    #: of the first intent the screen actually links with. Roles are CTA slots (`primary_cta`),
    #: structural parts (`card`, `logo`, `cart`) or `nav` / `trail` for the site's main
    #: navigation and breadcrumb trail.
    emits: dict[str, list[str]] = Field(default_factory=dict)
    responsive_behavior: ResponsiveBehavior = Field(default_factory=ResponsiveBehavior)
    implementation: ImplementationMapping
    animation_capabilities: list[str] = Field(default_factory=lambda: ["fade", "fade_up"])
    design_metadata: DesignMetadata = Field(default_factory=DesignMetadata)

    @model_validator(mode="after")
    def _default_variant_in_variants(self) -> ComponentDefinition:
        if self.default_variant not in self.variants:
            if "default_variant" in self.model_fields_set:
                raise ValueError(
                    f"{self.id}: default_variant '{self.default_variant}' not in variants"
                )
            object.__setattr__(self, "default_variant", self.variants[0])
        return self

    def supports_domain(self, domain: str) -> bool:
        return "*" in self.supported_domains or domain in self.supported_domains

    def slot_names(self) -> set[str]:
        return {s.name for s in self.slots}
