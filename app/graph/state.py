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
    ScreenPlan,
    UXPlan,
    VerificationResult,
)
from app.retrieval.models import RetrievedContext


class ScreenState(TypedDict, total=False):
    """One planned screen on its way through build -> resolve -> render -> verify -> fix."""

    run_id: str
    #: The user's brief, verbatim: product and brand names in it reach the copywriter.
    user_requirement: str
    clarified_requirements: ClarifiedRequirements
    design_direction: DesignDirection
    screen: ScreenPlan
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


class AgentState(TypedDict, total=False):
    run_id: str
    user_requirement: str
    user_answers: dict[str, str]
    clarifier_output: ClarifierOutput | None
    clarified_requirements: ClarifiedRequirements | None
    ux_plan: UXPlan | None
    design_direction: DesignDirection | None
    #: Final state of every planned screen, in plan order.
    screens: Annotated[list[ScreenState], operator.add]
    learning_events: Annotated[list[LearningEvent], operator.add]
    errors: Annotated[list[str], operator.add]
    usage: Annotated[list[dict[str, float | str]], operator.add]
