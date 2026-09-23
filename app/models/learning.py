from datetime import datetime
from typing import Literal

from pydantic import Field

from app.models.common import StrictModel

LessonStatus = Literal["candidate", "validated", "trusted"]


class LearningEvent(StrictModel):
    kind: Literal["fix_verified", "fix_failed", "lesson_applied"]
    target: str
    problem: str
    fix: str | None = None
    occurred_at: datetime
    context: dict[str, str] = Field(default_factory=dict)


class Lesson(StrictModel):
    """A reusable design rule: in this scope, this problem was fixed by this patch.

    Text, scope and fix are templated from registry ids, check names and patch values only, so a
    shared store never holds a tenant's product names, copy or model prose."""

    id: str
    text: str
    scope: dict[str, str] = Field(default_factory=dict)  # domain, page_type, component, problem
    fix: dict[str, str] = Field(default_factory=dict)  # property, value
    status: LessonStatus = "candidate"
    confirmations: int = 0
    violations: int = 0
    evidence: list[str] = Field(default_factory=list)  # run ids, most recent last
