"""The content model: what the product lists, written once per run so every screen shows the
same things. Generic over domains: a shop has `products`, a school `courses`, a SaaS `plans`."""

from __future__ import annotations

from pydantic import Field

from app.models.common import StrictModel


class Attribute(StrictModel):
    """One fact about an item, e.g. Roast: medium. A list, not a dict: strict structured-output
    schemas allow no free-form keys."""

    label: str
    value: str


class ContentItem(StrictModel):
    #: Slug, unique within its collection; the `:id` in a per-item route.
    id: str
    title: str
    subtitle: str = ""
    price: str | None = None
    badge: str | None = None
    #: The photograph to find, as the imagery service expects it.
    image: str
    #: Short lowercase facets for filtering and search, e.g. "single origin", "b2", "speaking".
    tags: list[str] = Field(default_factory=list)
    #: Facts for a detail page, e.g. Level: B2, Duration: 8 weeks.
    attributes: list[Attribute] = Field(default_factory=list)
    #: The photograph a screen found for this item; set when the site is assembled, so the
    #: item's own page and the cart show the picture its card shows.
    image_url: str | None = None


class Collection(StrictModel):
    #: snake_case name: products, courses, plans, articles.
    id: str
    #: What one item is called, e.g. "product", "course".
    item_label: str
    items: list[ContentItem] = Field(min_length=1)

    def find(self, item_id: str) -> ContentItem | None:
        return next((i for i in self.items if i.id == item_id), None)


class ContentModel(StrictModel):
    #: The brand as written on the wordmark.
    brand: str
    collections: list[Collection] = Field(default_factory=list)

    def collection(self, collection_id: str) -> Collection | None:
        return next((c for c in self.collections if c.id == collection_id), None)

    def locate(self, item_id: str) -> tuple[Collection, ContentItem] | None:
        for c in self.collections:
            if (item := c.find(item_id)) is not None:
                return c, item
        return None


class ItemBinding(StrictModel):
    """A section bound to one item of a collection: the card for it, or the page about it."""

    collection: str
    item: str
