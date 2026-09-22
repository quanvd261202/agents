from typing import Literal

from pydantic import Field

from app.models.common import StrictModel


class ClarifyingQuestion(StrictModel):
    question: str
    options: list[str] = Field(default_factory=list)
    default: str | None = None


class ClarifiedRequirements(StrictModel):
    product: str
    domain: str
    target_audience: str
    primary_goal: str
    key_features: list[str] = Field(default_factory=list)
    brand_notes: str | None = None
    constraints: list[str] = Field(default_factory=list)


class ClarifierOutput(StrictModel):
    status: Literal["ready", "needs_clarification"]
    questions: list[ClarifyingQuestion] = Field(default_factory=list, max_length=3)
    assumptions: list[str] = Field(default_factory=list)
    clarified_requirements: ClarifiedRequirements | None = None
