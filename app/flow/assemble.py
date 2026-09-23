"""Fan-in: the run's screens become one site. Deterministic."""

from __future__ import annotations

from typing import Any

from app.models.content import ContentModel
from app.models.plan import UXPlan
from app.models.render import RenderModel, RenderNode
from app.models.site import SiteMap, SiteModel


def assemble_site(
    plan: UXPlan, content: ContentModel | None, models: dict[str, RenderModel]
) -> SiteModel:
    """One SiteModel: the site map, the content model with the photographs the screens found for
    its items, and every resolved screen by id."""
    return SiteModel(
        site=SiteMap.from_plan(plan), content=with_image_urls(content, models), screens=models
    )


def with_image_urls(
    content: ContentModel | None, models: dict[str, RenderModel]
) -> ContentModel | None:
    """A bound card carries the photograph the imagery service found for its item; the content
    model learns it, so the item's own page and the cart show the same picture."""
    if content is None:
        return None
    urls: dict[str, str] = {}
    for model in models.values():
        _collect(model.root, urls)
    if not urls:
        return content
    collections = [
        c.model_copy(
            update={
                "items": [
                    i.model_copy(update={"image_url": urls[i.id]}) if i.id in urls else i
                    for i in c.items
                ]
            }
        )
        for c in content.collections
    ]
    return content.model_copy(update={"collections": collections})


def _collect(node: RenderNode, urls: dict[str, str]) -> None:
    binding = node.props.get("binding")
    images: Any = node.props.get("images")
    if isinstance(binding, dict) and isinstance(images, dict):
        item = binding.get("item")
        for slot in ("image", "media"):
            refs = images.get(slot)
            if isinstance(item, str) and item not in urls and refs and refs[0].get("url"):
                urls[item] = refs[0]["url"]
                break
    for child in node.children:
        _collect(child, urls)
