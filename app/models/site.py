"""The site map: the plan's screens as the deterministic engine sees them. Screen id is the
identity; the route is a property. Built from the UX plan, never edited by a model."""

from __future__ import annotations

from pydantic import Field

from app.models.common import StrictModel
from app.models.content import ContentModel
from app.models.plan import Link, UXPlan
from app.models.render import RenderModel


def default_route(screen_id: str, first: bool) -> str:
    """The route a screen gets when the planner gave none: the first is the entry."""
    return "/" if first else "/" + screen_id.replace("_", "-")


class SiteScreen(StrictModel):
    id: str
    route: str
    nav_label: str | None = None
    links: list[Link] = Field(default_factory=list)


class NavItem(StrictModel):
    screen: str
    label: str
    href: str


class SiteMap(StrictModel):
    #: The screen at "/".
    entry: str
    screens: list[SiteScreen] = Field(min_length=1)

    @classmethod
    def from_plan(cls, plan: UXPlan) -> SiteMap:
        has_entry = any(s.route == "/" for s in plan.screens)
        screens = [
            SiteScreen(
                id=s.id,
                route=s.route or default_route(s.id, i == 0 and not has_entry),
                nav_label=s.nav_label,
                links=list(s.links),
            )
            for i, s in enumerate(plan.screens)
        ]
        entry = next((s.id for s in screens if s.route == "/"), screens[0].id)
        return cls(entry=entry, screens=screens)

    def screen(self, screen_id: str) -> SiteScreen:
        for s in self.screens:
            if s.id == screen_id:
                return s
        raise KeyError(f"no screen '{screen_id}' in the site map")

    def route(self, screen_id: str) -> str:
        return self.screen(screen_id).route

    def nav(self) -> list[NavItem]:
        """Main navigation, in plan order: every screen with a label."""
        return [
            NavItem(screen=s.id, label=s.nav_label, href=s.route)
            for s in self.screens
            if s.nav_label
        ]

    def target(self, screen_id: str, intents: list[str]) -> str | None:
        """The screen reached by the first of `intents` that `screen_id` links with, if any."""
        links = self.screen(screen_id).links
        for intent in intents:
            if intent == "go_home":
                return self.entry  # every screen can go home, the entry included
            for link in links:
                if link.intent == intent:
                    return link.to
        return None

    def href(self, screen_id: str, item_id: str | None = None) -> str | None:
        """The target's route with its item parameter filled; None when the route needs an item
        and there is none to put in it."""
        parts = []
        for seg in self.route(screen_id).split("/"):
            if seg.startswith(":"):
                if item_id is None:
                    return None
                seg = item_id
            parts.append(seg)
        return "/".join(parts) or "/"

    def trail(self, screen_id: str) -> list[str]:
        """Breadcrumb trail: entry, then the screen that opens this one per item, then itself."""
        trail = [self.entry]
        for s in self.screens:
            if s.id in (screen_id, self.entry):
                continue
            if any(link.to == screen_id and link.intent == "open_item" for link in s.links):
                trail.append(s.id)
                break
        if screen_id != self.entry:
            trail.append(screen_id)
        return trail


class SiteModel(StrictModel):
    """The assembled site: what `uib view` serves and the flow check walks."""

    site: SiteMap
    content: ContentModel | None = None
    #: Resolved screens by screen id.
    screens: dict[str, RenderModel] = Field(default_factory=dict)


class CartLine(StrictModel):
    item: str
    qty: int = 1


class RuntimeState(StrictModel):
    """What the visitor does on the site: separate from every RenderModel. The renderer seeds it
    for screenshots; the frontend keeps it per viewer."""

    cart: list[CartLine] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    query: str = ""


class RenderContext(StrictModel):
    """What a screen is rendered inside of for its screenshot: its site, the content and a seeded
    runtime state, so the navigation shows real links and a cart page shows lines. Nothing here
    enters the RenderModel."""

    site: SiteMap
    content: ContentModel | None = None
    state: RuntimeState = Field(default_factory=RuntimeState)
