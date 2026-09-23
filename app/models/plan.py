from pydantic import Field

from app.models.common import StrictModel


class Link(StrictModel):
    """One edge out of a screen: what the visitor means to do, and which screen that reaches."""

    intent: str
    to: str


class JourneyStep(StrictModel):
    screen: str
    intent: str
    to: str


class ScreenPlan(StrictModel):
    id: str
    purpose: str
    key_content: list[str] = Field(default_factory=list)
    interactions: list[str] = Field(default_factory=list)
    #: URL path. The entry screen is "/"; a screen opened per item carries an :id segment.
    route: str | None = None
    #: Label in the main navigation; None keeps the screen out of it (checkout, say).
    nav_label: str | None = None
    links: list[Link] = Field(default_factory=list)


class UXPlan(StrictModel):
    product: str
    user_goals: list[str]
    #: The primary path through the product, each step one of its screen's links.
    journey: list[JourneyStep] = Field(default_factory=list)
    screens: list[ScreenPlan] = Field(min_length=1)

    def screen(self, screen_id: str) -> ScreenPlan:
        for s in self.screens:
            if s.id == screen_id:
                return s
        raise KeyError(f"no screen '{screen_id}' in the plan")
