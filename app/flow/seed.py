"""The runtime state a screenshot is taken with. A cart page captured empty would verify an
empty state, so the renderer seeds the cart from the content model; nothing of this reaches a
RenderModel or a spec."""

from __future__ import annotations

from app.models.content import ContentModel
from app.models.site import CartLine, RuntimeState


def default_runtime_state(content: ContentModel | None) -> RuntimeState:
    if content is None or not content.collections:
        return RuntimeState()
    items = content.collections[0].items
    lines = [CartLine(item=item.id, qty=qty) for item, qty in zip(items[:2], (1, 2), strict=False)]
    return RuntimeState(cart=lines)
