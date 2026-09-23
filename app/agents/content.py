"""M13 - Content Model. Writes what the product lists, once per run.

Runs after the Design Director and before the screens fan out, so the listing, the detail page
and the cart all show the same things with the same names and prices. Generic over domains: the
collections are whatever the product offers (products, courses, plans, articles). The
Copywriter binds list sections to items from here instead of inventing its own."""

from __future__ import annotations

import re

from app.agents.base import Agent, brief_block
from app.core.exceptions import ValidationError
from app.core.llm import LLMProvider
from app.models.content import ContentModel
from app.models.plan import UXPlan
from app.models.requirements import ClarifiedRequirements

SYSTEM = """You are the product's content editor. You decide what it lists and write that catalogue
once, so every screen shows the same things.

Return:
- `brand`: the name on the wordmark. The brief's own brand name when it gives one; otherwise a
  short, plausible one for this product. Never a placeholder.
- `collections`: the kinds of thing a visitor browses, opens and buys or enrols in - products,
  courses, plans, articles. Only kinds the screens below actually list; most products have one,
  none has more than three. A product that lists nothing (a settings page, a dashboard alone)
  returns no collections.

Each collection: `id` in snake_case (products, courses), `item_label` for one item (product,
course), and `items`: {count} for the main collection, at least 4 for any other. Each item:
- `id`: a URL slug, lowercase words joined by hyphens, unique in the collection
- `title`: the real name, distinct from every other title
- `subtitle`: one short line a card shows under the name
- `price`: in one currency, like $24 or $24.00, when the item is sold; null when it is not
- `badge`: New, Bestseller, Limited, Popular... on a few items; null on most
- `image`: the photograph to find in a stock library: concrete subject, setting and mood in four
  to ten words, no brand names, no text in the picture
- `tags`: 2-5 short lowercase facets a visitor filters or searches by (a category, a level, an
  origin, a skill), from one shared vocabulary across the collection so a filter narrows it
- `attributes`: 2-5 {{label, value}} facts a detail page shows (Roast: medium, Duration: 8 weeks)

Write for this product and this audience. Specific beats generic. Never lorem ipsum, never
"Product 1", never "[brand]". Vary the items: different prices, tags and badges, not one item
renamed twelve times."""

USER = """Product: {product} ({domain}), for {audience}. Goal: {goal}
Key features: {features}
Brand notes: {brand}

Screens, with what each shows:
{screens}{brief}"""

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")


class ContentModelAgent(Agent):
    """Satisfies app.services.interfaces.ContentModelService."""

    name = "content_model"

    def __init__(self, llm: LLMProvider, items_per_collection: int = 12) -> None:
        super().__init__(llm)
        self._count = items_per_collection

    async def compose(
        self, req: ClarifiedRequirements, plan: UXPlan, brief: str = ""
    ) -> ContentModel:
        screens = "\n".join(
            f"- {s.id}: {s.purpose}"
            + (f"; shows {', '.join(s.key_content)}" if s.key_content else "")
            for s in plan.screens
        )
        return await self._invoke(
            SYSTEM.format(count=self._count),
            USER.format(
                product=req.product,
                domain=req.domain,
                audience=req.target_audience,
                goal=req.primary_goal,
                features=", ".join(req.key_features) or "(none stated)",
                brand=req.brand_notes or "(none stated)",
                screens=screens,
                brief=brief_block(brief),
            ),
            ContentModel,
            self._validate,
        )

    @staticmethod
    def _validate(model: ContentModel) -> ContentModel:
        if not model.brand.strip() or _is_placeholder(model.brand):
            raise ValidationError("`brand` must be the real wordmark", target="brand")
        if len(model.collections) > 3:
            raise ValidationError("at most three collections", target="collections")
        ids = [c.id for c in model.collections]
        if len(ids) != len(set(ids)):
            raise ValidationError(f"duplicate collection ids: {ids}", target="collections")
        for c in model.collections:
            if not _SNAKE.match(c.id):
                raise ValidationError(
                    f"collection id '{c.id}' must be snake_case, e.g. products", target=c.id
                )
            if len(c.items) < 4:
                raise ValidationError(
                    f"collection '{c.id}' has {len(c.items)} items; write at least 4", target=c.id
                )
            slugs = [i.id for i in c.items]
            if len(slugs) != len(set(slugs)):
                raise ValidationError(f"duplicate item ids in '{c.id}': {slugs}", target=c.id)
            titles = [i.title.strip().lower() for i in c.items]
            if len(titles) != len(set(titles)):
                raise ValidationError(
                    f"duplicate item titles in '{c.id}'; every item has its own name", target=c.id
                )
            for item in c.items:
                if not _SLUG.match(item.id):
                    raise ValidationError(
                        f"item id '{item.id}' in '{c.id}' must be a slug like house-blend",
                        target=c.id,
                    )
                if _is_placeholder(item.title) or not item.image.strip():
                    raise ValidationError(
                        f"item '{item.id}' in '{c.id}' needs a real title and an image description",
                        target=c.id,
                    )
        return model


def _is_placeholder(text: str) -> bool:
    t = text.lower()
    return "lorem" in t or "[brand]" in t or any(f"product {n}" in t for n in "123456789")
