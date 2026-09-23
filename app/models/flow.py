"""M13 flow models: what the flow check found, and the patches a fixer may propose to the site
plan. The plan itself is only ever replaced by a validated result of applying patches."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.models.common import StrictModel


class FlowStep(StrictModel):
    """One journey step walked in the browser."""

    screen: str
    intent: str
    to: str
    ok: bool
    detail: str = ""


class DeadControl(StrictModel):
    """A control that emits an intent the screen never links: it renders, but leads nowhere."""

    screen: str
    role: str
    #: Semantic type of the section holding it (`hero`, `navigation`...).
    section: str
    text: str = ""


class FlowReport(StrictModel):
    steps: list[FlowStep] = Field(default_factory=list)
    dead: list[DeadControl] = Field(default_factory=list)
    #: Anchors that still point at a same-page hash, per screen: informational.
    anchors: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return not self.errors and all(s.ok for s in self.steps)

    def failed_steps(self) -> list[FlowStep]:
        return [s for s in self.steps if not s.ok]


PatchOp = Literal["add_edge", "retarget_edge", "set_route"]


class SitePlanPatch(StrictModel):
    """One change to the site plan. `add_edge`: screen gains {intent, to}. `retarget_edge`: the
    screen's link with `intent` now points at `to`. `set_route`: the screen's route becomes
    `route`."""

    op: PatchOp
    screen: str
    intent: str | None = None
    to: str | None = None
    route: str | None = None


class FlowFixResult(StrictModel):
    status: Literal["success", "failure"]
    patches: list[SitePlanPatch] = Field(default_factory=list)
    reason: str | None = None
    #: "rule" when deterministic repair rules wrote the patches; "model" when the agent did.
    source: Literal["rule", "model"] = "rule"
