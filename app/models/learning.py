from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.common import StrictModel


class LearningEvent(StrictModel):
    kind: Literal["fix_verified", "fix_failed", "lesson_applied"]
    target: str
    problem: str
    fix: str | None = None
    occurred_at: datetime
    context: dict[str, str] = Field(default_factory=dict)


class Lesson(StrictModel):
    id: str
    text: str
    scope: dict[str, str] = Field(default_factory=dict)
    status: Literal["candidate", "validated", "trusted"] = "candidate"
    confirmations: int = 0
    violations: int = 0
