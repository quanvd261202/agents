from typing import Literal

from pydantic import Field

from app.models.common import Dimension, Severity, StrictModel


class Issue(StrictModel):
    severity: Severity
    dimension: Dimension
    target: str
    issue: str
    suggestion: str
    deterministic: bool = False


class VerificationResult(StrictModel):
    status: Literal["pass", "needs_fix"]
    issues: list[Issue] = Field(default_factory=list)


class Patch(StrictModel):
    target: str
    property: str
    value: str | int | dict[str, str]


class FixResult(StrictModel):
    status: Literal["success", "failure"]
    patches: list[Patch] = Field(default_factory=list)
    reason: str | None = None
    #: "model" when the fixer agent wrote the patches; "lesson" when trusted lessons were applied
    #: deterministically and no model was called.
    source: Literal["model", "lesson"] = "model"
    lesson_ids: list[str] = Field(default_factory=list)
