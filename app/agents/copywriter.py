"""M10 - Copywriter. Writes the words on one built screen and describes its photographs.

Runs after the Design Builder, which owns structure, and before the imagery service, which turns
the image descriptions written here into photographs. The output only ever adds `content` to the
sections the builder chose (and product cards under sections that list products), so it cannot
change what the page is, only what it says.

M13: when the run has a content model, sections that list or show one item bind to its items by
id instead of inventing products, so every screen agrees on names, prices and pictures."""

from __future__ import annotations

from datetime import date

from pydantic import Field

from app.agents.base import Agent, brief_block
from app.catalog.registry import ComponentRegistry
from app.core.exceptions import ValidationError
from app.core.llm import LLMProvider
from app.models.common import StrictModel
from app.models.content import ContentItem, ContentModel, ItemBinding
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
- Every section gets copy. A component's built-in text is placeholder copy for a different
  business, so every slot the visitor reads (logo, headline, title, subhead, subtitle, body,
  description, tagline, items, calls to action) is written for every section listed. Only UI
  labels (size_label, sort_label...) may be left to their defaults.
- A section marked `item_ids: pick N` lists things from the product's collections below: return
  `item_ids` (a field of the section beside `slots`, never a slot name) with N ids from one
  collection, and leave `items` empty. A section marked `item_ids: the one item` is about a
  single thing: return exactly one id. Cards and buy boxes take their names, prices, badges and
  pictures from the collection, so the screen agrees with every other screen.
- Only when no collection exists, a section marked `items: N product cards` takes `items`: N
  products, each with a title, a short note, a price, an optional badge (New, Bestseller,
  Limited...) and an image description. Every other section leaves `items` and `item_ids` empty.
- The brand, when given, is the wordmark: the `logo` slot is exactly that name.
- Write only for the sections listed below, by their exact ids.
- Names, prices, currency and voice stay consistent across the whole screen."""

USER = """Product: {product} ({domain}), for {audience}. Goal: {goal}
Key features: {features}
Brand notes: {brand}
Visual direction: {style}
Today: {today}

Screen: {screen_id} - {purpose}
Key content: {content}
Interactions: {interactions}

{collections}Sections and their slots, `name (format)`:
{sections}{brief}"""

COLLECTIONS = """Brand: {brand}
Collections (`id - title - price`):
{lines}

"""

#: The one component that lists products; sections allowing it as a child take `items`.
ITEM_CHILD = "product_card"
#: Slots whose text the visitor reads as the product's own words. A section offering any of
#: them must receive copy, or its component's placeholder text (written for another business)
#: would ship as if it were content.
READ_SLOTS = frozenset(
    {"logo", "headline", "title", "subhead", "subtitle", "body", "description", "tagline"}
)


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
    #: Ids from one collection of the content model; replaces `items` when collections exist.
    item_ids: list[str] = Field(default_factory=list)


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
        content: ContentModel | None = None,
    ) -> DesignSpec:
        # Binding only happens when there is something to bind to; a brand alone is still shown.
        bound = content if content is not None and content.collections else None
        user = USER.format(
            product=req.product,
            domain=req.domain,
            audience=req.target_audience,
            goal=req.primary_goal,
            features=", ".join(req.key_features) or "(none stated)",
            brand=req.brand_notes or "(none stated)",
            style=direction.visual_style,
            today=date.today().isoformat(),
            screen_id=screen.id,
            purpose=screen.purpose,
            content=", ".join(screen.key_content) or "(not specified)",
            interactions=", ".join(screen.interactions) or "(not specified)",
            collections=_collections_block(content) if content is not None else "",
            sections=self._section_lines(spec, bound is not None),
            brief=brief_block(brief),
        )
        out = await self._invoke(SYSTEM, user, CopyOutput, lambda o: self._validate(o, spec, bound))
        return self._assemble(out, spec, bound)

    def _section_lines(self, spec: DesignSpec, bound: bool) -> str:
        lines = []
        for s in spec.sections:
            comp = self._components.get(s.type)
            slots = ", ".join(
                f"{sl.name} ({sl.description})" if sl.description else sl.name for sl in comp.slots
            )
            line = f"- {s.id} ({comp.id}, variant {s.variant or comp.default_variant}): "
            line += slots or "(no slots)"
            if ITEM_CHILD in comp.allowed_children:
                n = item_count(comp.id, s.variant)
                line += f"; item_ids: pick {n}" if bound else f"; items: {n} product cards"
            elif comp.binds and bound:
                line += "; item_ids: the one item"
            lines.append(line)
        return "\n".join(lines)

    # -------------------------------------------------------------------------------------
    def _validate(
        self, out: CopyOutput, spec: DesignSpec, content: ContentModel | None
    ) -> CopyOutput:
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
            lists = ITEM_CHILD in comp.allowed_children
            if sc.items and not lists:
                raise ValidationError(
                    f"{comp.id} in '{sc.id}' does not list products; drop its items", target=sc.id
                )
            _validate_binding(sc, comp.id, lists, bool(comp.binds), content)
            texts = [c.text for c in sc.slots] + [i.title for i in sc.items]
            if any(_is_placeholder(t) for t in texts):
                raise ValidationError(
                    f"placeholder copy in '{sc.id}': write the real words", target=sc.id
                )
        written = {sc.id: {c.slot for c in sc.slots if c.text.strip()} for sc in out.sections}
        bound_ids = {sc.id for sc in out.sections if sc.item_ids}
        silent = [
            s.id
            for s in spec.sections
            if s.id not in bound_ids  # a bound section's title comes from its item
            and (readable := READ_SLOTS & self._components.get(s.type).slot_names())
            and not (written.get(s.id, set()) & readable)
        ]
        if silent:
            raise ValidationError(
                f"no copy for {silent}: each needs its own words in at least one of "
                f"{sorted(READ_SLOTS)}; the component's built-in text is a placeholder for "
                "another business",
                target=silent[0],
            )
        return out

    def _assemble(
        self, out: CopyOutput, spec: DesignSpec, content: ContentModel | None
    ) -> DesignSpec:
        by_id = {sc.id: sc for sc in out.sections}
        sections = []
        for s in spec.sections:
            sc = by_id.get(s.id)
            if sc is None:
                sections.append(s)
                continue
            written = {c.slot: c.text.strip() for c in sc.slots if c.text.strip()}
            update: dict[str, object] = {"content": {**s.content, **written}}
            variant = "premium" if s.variant == "premium" else None
            if sc.items:
                update["children"] = [
                    _card(s.id, i, item, variant) for i, item in enumerate(sc.items, 1)
                ]
            elif sc.item_ids and content is not None:
                comp = self._components.get(s.type)
                located = [content.locate(i) for i in sc.item_ids]
                bound = [b for b in located if b is not None]  # validated: all present
                if ITEM_CHILD in comp.allowed_children:
                    binds = self._components.get(ITEM_CHILD).binds
                    update["children"] = [
                        _bound_card(s.id, i, coll.id, item, variant, binds)
                        for i, (coll, item) in enumerate(bound, 1)
                    ]
                else:
                    # The section is about this item: its facts win over anything written.
                    coll, item = bound[0]
                    update["binding"] = ItemBinding(collection=coll.id, item=item.id)
                    update["content"] = {**written, **_bound_slots(item, comp.binds)}
                    update["content"] = {**s.content, **update["content"]}  # type: ignore[dict-item]
            sections.append(s.model_copy(update=update))
        return spec.model_copy(update={"sections": sections})


def _validate_binding(
    sc: SectionCopy, component_id: str, lists: bool, binds: bool, content: ContentModel | None
) -> None:
    if content is None:
        if sc.item_ids:
            raise ValidationError(
                f"'{sc.id}' has item_ids but this product has no collections; "
                + ("write `items` instead" if lists else "drop them"),
                target=sc.id,
            )
        return
    if sc.item_ids and not (lists or binds):
        raise ValidationError(
            f"{component_id} in '{sc.id}' shows no items; drop its item_ids", target=sc.id
        )
    if lists:
        if sc.items:
            raise ValidationError(
                f"'{sc.id}' must pick item_ids from the collections, not write items",
                target=sc.id,
            )
        if not sc.item_ids:
            raise ValidationError(f"'{sc.id}' lists items: pick their item_ids", target=sc.id)
    elif binds and len(sc.item_ids) != 1:
        raise ValidationError(
            f"'{sc.id}' is about one item: give exactly one id in item_ids", target=sc.id
        )
    if len(sc.item_ids) != len(set(sc.item_ids)):
        raise ValidationError(f"'{sc.id}' repeats an item id", target=sc.id)
    collections: set[str] = set()
    for item_id in sc.item_ids:
        found = content.locate(item_id)
        if found is None:
            raise ValidationError(
                f"'{sc.id}' names item '{item_id}', which is in no collection; ids: "
                f"{[i.id for c in content.collections for i in c.items]}",
                target=sc.id,
            )
        collections.add(found[0].id)
    if len(collections) > 1:
        raise ValidationError(
            f"'{sc.id}' mixes items from {sorted(collections)}; pick from one collection",
            target=sc.id,
        )


def _collections_block(content: ContentModel) -> str:
    if not content.collections:
        return f"Brand: {content.brand}\n\n"
    lines = []
    for c in content.collections:
        lines.append(f"{c.id} ({c.item_label}):")
        lines.extend(
            f"  {i.id} - {i.title}" + (f" - {i.price}" if i.price else "") for i in c.items
        )
    return COLLECTIONS.format(brand=content.brand, lines="\n".join(lines))


def _bound_slots(item: ContentItem, binds: dict[str, str]) -> dict[str, str]:
    """The item's fields in the slots the component declares for them; empty fields stay out."""
    values = {}
    for field, slot in binds.items():
        value = getattr(item, field, None)
        if isinstance(value, str) and value.strip():
            values[slot] = value.strip()
    return values


def _bound_card(
    parent: str,
    i: int,
    collection: str,
    item: ContentItem,
    variant: str | None,
    binds: dict[str, str],
) -> SectionSpec:
    return SectionSpec(
        id=f"{parent}-item-{i}",
        type=ITEM_CHILD,
        variant=variant,
        content=_bound_slots(item, binds),
        binding=ItemBinding(collection=collection, item=item.id),
    )


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
