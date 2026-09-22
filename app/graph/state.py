from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from app.models import (
    ClarifiedRequirements,
    ClarifierOutput,
    DesignDirection,
    DesignSpec,
    FixResult,
    LearningEvent,
    RenderModel,
    RenderResult,
    UXPlan,
    VerificationResult,
)


class RetrievedContext(TypedDict, total=False):
    components: list[str]
    layouts: list[str]
    lessons: list[str]


class AgentState(TypedDict, total=False):
    run_id: str
    user_requirement: str
    user_answers: dict[str, str]
    clarifier_output: ClarifierOutput | None
    clarified_requirements: ClarifiedRequirements | None
    ux_plan: UXPlan | None
    design_direction: DesignDirection | None
    retrieved_context: RetrievedContext | None
    design_spec: DesignSpec | None
    resolved_design: RenderModel | None
    render_result: RenderResult | None
    verification_result: VerificationResult | None
    fix_result: FixResult | None
    learning_events: Annotated[list[LearningEvent], operator.add]
    iteration: int
    errors: Annotated[list[str], operator.add]
    usage: Annotated[list[dict[str, float | str]], operator.add]
