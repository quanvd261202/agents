"""M10 - Copywriter. Writes the words on one built screen and describes its photographs.

Runs after the Design Builder, which owns structure, and before the imagery service, which turns
the image descriptions written here into photographs. The output only ever adds `content` to the
sections the builder chose (and product cards under sections that list products), so it cannot
change what the page is, only what it says."""

from __future__ import annotations

from pydantic import Field

from app.agents.base import Agent, brief_block
from app.catalog.registry import ComponentRegistry
from app.core.exceptions import ValidationError
from app.core.llm import LLMProvider
from app.models.common import StrictModel
from app.models.direction import DesignDirection
from app.models.dsl import DesignSpec, SectionSpec
from app.models.plan import ScreenPlan
from app.models.requirements import ClarifiedRequirements

SYSTEM = """You write the words on one screen of a product, as its own copywriter would. The screen
is already composed: you are given its sections and, for each, the slots its component can show.

You MUST NOT change structure: no new sections, no layout, no styling, no component or variant
choices. Return copy for the slots, per section.

Rules:
- Write for this product and this audience. Specific beats generic: real product names, real
  options, prices in one currency. Never lorem ipsum, never "Product 1", never "[brand]".
- Short. Headlines under eight words, subheads one sentence, body at most two sentences, labels
  one or two words. It is read on a phone.
- Respect each slot's format note. Comma-separated lists contain no other commas. Prices look
  like $24 or $24.00, ratings like 4.8, counts are plain numbers.
- Image slots (`media`, `image`) describe the photograph to find in a stock library: concrete
  subject, setting and mood in four to ten words, no brand names, no text in the picture. Where
  the slot asks for a list, comma-separate one description per entry (one per gallery shot, one
  per tile).
- Fill the slots that carry product-specific content. Skip a slot to keep the component's own
  default label; skip rather than pad.
- A section marked `items: N product cards` takes `items`: N products, each with a title, a short
  note, a price, an optional badge (New, Bestseller, Limited...) and an image description.
- Names, prices, currency and voice stay consistent across the whole screen."""

USER = """Product: {product} ({domain}), for {audience}. Goal: {goal}
Key features: {features}
Brand notes: {brand}
Visual direction: {style}

Screen: {screen_id} - {purpose}
Key content: {content}
Interactions: {interactions}

Sections and their slots, `name (format)`:
{sections}{brief}"""

#: The one component that lists products; sections allowing it as a child take `items`.
ITEM_CHILD = "product_card"


class SlotCopy(StrictModel):
    slot: str
    text: str


class ItemCopy(StrictModel):
    title: str
    note: str = ""
    price: str
    badge: str | None = None
    image: str


class SectionCopy(StrictModel):
    id: str
    slots: list[SlotCopy] = Field(default_factory=list)
    items: list[ItemCopy] = Field(default_factory=list)


class CopyOutput(StrictModel):
    sections: list[SectionCopy]


def item_count(component_id: str, variant: str | None) -> int:
    """How many product cards the component shows, so the model writes that many."""
    if component_id == "product_grid":
        return 8 if variant == "dense" else 6
    if component_id == "related_products":
        return 4 if variant == "grid" else 6
    if component_id == "cart_items":
        return 3
    return 4


class CopywriterAgent(Agent):
    """Satisfies app.services.interfaces.CopywriterService."""

    name = "copywriter"

    def __init__(self, llm: LLMProvider, components: ComponentRegistry) -> None:
        super().__init__(llm)
        self._components = components

    async def write(
        self,
        req: ClarifiedRequirements,
        screen: ScreenPlan,
        direction: DesignDirection,
        spec: DesignSpec,
        brief: str = "",
    ) -> DesignSpec:
        user = USER.format(
            product=req.product,
            domain=req.domain,
            audience=req.target_audience,
            goal=req.primary_goal,
            features=", ".join(req.key_features) or "(none stated)",
            brand=req.brand_notes or "(none stated)",
            style=direction.visual_style,
            screen_id=screen.id,
            purpose=screen.purpose,
            content=", ".join(screen.key_content) or "(not specified)",
            interactions=", ".join(screen.interactions) or "(not specified)",
            sections=self._section_lines(spec),
            brief=brief_block(brief),
        )
        out = await self._invoke(SYSTEM, user, CopyOutput, lambda o: self._validate(o, spec))
        return self._assemble(out, spec)

    def _section_lines(self, spec: DesignSpec) -> str:
        lines = []
        for s in spec.sections:
            comp = self._components.get(s.type)
            slots = ", ".join(
                f"{sl.name} ({sl.description})" if sl.description else sl.name for sl in comp.slots
            )
            line = f"- {s.id} ({comp.id}, variant {s.variant or comp.default_variant}): "
            line += slots or "(no slots)"
            if ITEM_CHILD in comp.allowed_children:
                line += f"; items: {item_count(comp.id, s.variant)} product cards"
            lines.append(line)
        return "\n".join(lines)

    # -------------------------------------------------------------------------------------
    def _validate(self, out: CopyOutput, spec: DesignSpec) -> CopyOutput:
        seen: set[str] = set()
        for sc in out.sections:
            if sc.id in seen:
                raise ValidationError(f"section '{sc.id}' appears twice", target=sc.id)
            seen.add(sc.id)
            section = spec.find(sc.id)
            if section is None:
                raise ValidationError(
                    f"'{sc.id}' is not a section of this screen; "
                    f"use only {[s.id for s in spec.sections]}",
                    target=sc.id,
                )
            comp = self._components.get(section.type)
            unknown = {c.slot for c in sc.slots} - comp.slot_names()
            if unknown:
                raise ValidationError(
                    f"{comp.id} has no slot {sorted(unknown)}; "
                    f"its slots: {sorted(comp.slot_names())}",
                    target=sc.id,
                )
            if sc.items and ITEM_CHILD not in comp.allowed_children:
                raise ValidationError(
                    f"{comp.id} in '{sc.id}' does not list products; drop its items", target=sc.id
                )
            texts = [c.text for c in sc.slots] + [i.title for i in sc.items]
            if any(_is_placeholder(t) for t in texts):
                raise ValidationError(
                    f"placeholder copy in '{sc.id}': write the real words", target=sc.id
                )
        return out

    @staticmethod
    def _assemble(out: CopyOutput, spec: DesignSpec) -> DesignSpec:
        by_id = {sc.id: sc for sc in out.sections}
        sections = []
        for s in spec.sections:
            sc = by_id.get(s.id)
            if sc is None:
                sections.append(s)
                continue
            written = {c.slot: c.text.strip() for c in sc.slots if c.text.strip()}
            update: dict[str, object] = {"content": {**s.content, **written}}
            if sc.items:
                variant = "premium" if s.variant == "premium" else None
                update["children"] = [
                    _card(s.id, i, item, variant) for i, item in enumerate(sc.items, 1)
                ]
            sections.append(s.model_copy(update=update))
        return spec.model_copy(update={"sections": sections})


def _card(parent: str, i: int, item: ItemCopy, variant: str | None) -> SectionSpec:
    content = {
        "image": item.image.strip(),
        "title": item.title.strip(),
        "price": item.price.strip(),
    }
    if item.note.strip():
        content["note"] = item.note.strip()
    if item.badge and item.badge.strip():
        content["badge"] = item.badge.strip()
    return SectionSpec(id=f"{parent}-item-{i}", type=ITEM_CHILD, variant=variant, content=content)


def _is_placeholder(text: str) -> bool:
    t = text.lower()
    return "lorem" in t or "[brand]" in t or any(f"product {n}" in t for n in "123456789")
