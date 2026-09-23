from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from app.models import (
    ClarifiedRequirements,
    ClarifierOutput,
    ContentModel,
    DesignDirection,
    DesignSpec,
    FixResult,
    FlowFixResult,
    FlowReport,
    LearningEvent,
    RenderModel,
    RenderResult,
    ScreenPlan,
    SiteMap,
    SiteModel,
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
    content_model: ContentModel | None
    #: Routes and links of every planned screen: the resolver wires hrefs from it.
    site_map: SiteMap
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
    #: What the product lists, decided once so every screen shows the same things.
    content_model: ContentModel | None
    #: Final state of every planned screen, in plan order.
    screens: Annotated[list[ScreenState], operator.add]
    #: The assembled site, the walk through its journeys and the plan repair, if one was needed.
    site_model: SiteModel | None
    flow_report: FlowReport | None
    flow_fix: FlowFixResult | None
    learning_events: Annotated[list[LearningEvent], operator.add]
    errors: Annotated[list[str], operator.add]
    usage: Annotated[list[dict[str, float | str]], operator.add]
