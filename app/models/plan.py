from pydantic import Field

from app.models.common import StrictModel


class ScreenPlan(StrictModel):
    id: str
    purpose: str
    key_content: list[str] = Field(default_factory=list)
    interactions: list[str] = Field(default_factory=list)


class UXPlan(StrictModel):
    product: str
    user_goals: list[str]
    journey: list[str]
    screens: list[ScreenPlan] = Field(min_length=1)
