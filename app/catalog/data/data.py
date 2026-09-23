"""Data components. Implementation mappings live here, never in agents."""

from app.catalog.data._helpers import (  # noqa: F401
    _ALL,
    _CARD_ANIMS,
    C,
    ComponentDefinition,
    DesignMetadata,
    ResponsiveBehavior,
    S,
    _impl,
)

_APP = ["saas", "dashboard", "admin"]
_GRID_RULES = ResponsiveBehavior(
    rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}, "desktop": {"columns": 4}}
)

COMPONENTS: list[ComponentDefinition] = [
    ComponentDefinition(
        id="stats",
        category=C.data,
        description=(
            "Row of KPI stat cards: label, headline value and a colour-coded delta against a "
            "period. standard adds an icon per card, with_trend a sparkline per card, compact "
            "packs every metric into one hairline-divided strip."
        ),
        capabilities=["stats", "dashboard", "analytics", "kpi", "trend", "sparkline"],
        supported_domains=_APP,
        variants=["standard", "with_trend", "compact"],
        slots=[
            S(name="title", description="accessible name of the metrics row"),
            S(name="labels", description="comma list of metric names"),
            S(name="values", description="comma list of headline values, same order"),
            S(name="deltas", description="comma list of changes, e.g. +12.4%,-0.4%"),
            S(name="period", description="comparison caption, e.g. 'vs last month'"),
        ],
        implementation=_impl(
            "Stats",
            ("Card", "shadcn"),
            ("NumberTicker", "magicui"),
            ("Sparkline", "native", "inline SVG trend line"),
        ),
        animation_capabilities=["fade", "fade_up", "number_ticker", "stagger"],
        responsive_behavior=_GRID_RULES,
    ),
    ComponentDefinition(
        id="chart_panel",
        category=C.data,
        description=(
            "Primary visualization card: title, headline value with delta, time-range control, "
            "and an inline SVG chart with axes, gridlines, legend and hover tooltip. line "
            "compares two periods, area shows one trend, bar shows discrete periods, donut "
            "shows part-to-whole with a value legend."
        ),
        capabilities=["analytics", "charts", "dashboard", "trend", "comparison", "breakdown"],
        supported_domains=_APP,
        variants=["line", "bar", "area", "donut"],
        default_variant="line",
        slots=[
            S(name="title", description="chart title, e.g. Revenue"),
            S(name="subtitle", description="what is measured and over which period"),
            S(name="value", description="headline total"),
            S(name="delta", description="change vs the comparison period"),
            S(name="note", description="comparison caption, or the donut centre label"),
            S(name="labels", description="comma list of x-axis labels or donut segment names"),
            S(name="values", description="comma list of numbers for the main series"),
            S(name="compare_values", description="comma list of numbers for the comparison (line)"),
            S(name="series", description="comma list of series names"),
            S(name="ranges", description="comma list of time-range options, e.g. 7D,30D,12M"),
        ],
        implementation=_impl(
            "ChartPanel",
            ("Card", "shadcn"),
            ("Chart", "native", "inline SVG line/area/bar/donut"),
            ("ToggleGroup", "radix", "time range"),
        ),
        animation_capabilities=["fade", "fade_up", "reveal", "none"],
    ),
    ComponentDefinition(
        id="kpi_hero",
        category=C.data,
        description=(
            "One headline metric given the whole width: large value, trend, context line and a "
            "chart. standard pairs it with an area chart against last year; split puts the value "
            "and a breakdown beside a bar chart with a goal line."
        ),
        capabilities=["kpi", "headline_metric", "dashboard", "analytics", "trend", "goal"],
        supported_domains=_APP,
        variants=["standard", "split"],
        slots=[
            S(name="label", required=True, description="metric name"),
            S(name="value", required=True, description="headline value"),
            S(name="delta", description="change vs comparison"),
            S(name="context", description="comparison sentence"),
            S(name="labels", description="comma list of x-axis labels"),
            S(name="values", description="comma list of numbers"),
            S(name="compare_values", description="comma list of comparison numbers (standard)"),
            S(name="series", description="main series name (standard)"),
            S(name="compare_series", description="comparison series name (standard)"),
            S(name="breakdown", description="comma list of three supporting metric names (split)"),
            S(name="chart_title", description="chart caption (split)"),
            S(name="target", description="goal value drawn as a line (split)"),
            S(name="target_label", description="goal line label (split)"),
        ],
        implementation=_impl(
            "KpiHero",
            ("Card", "shadcn"),
            ("NumberTicker", "magicui"),
            ("Chart", "native", "inline SVG area/bar chart"),
            ("ToggleGroup", "radix", "time range"),
        ),
        animation_capabilities=["fade", "fade_up", "number_ticker", "reveal", "none"],
    ),
    ComponentDefinition(
        id="data_table",
        category=C.data,
        description=(
            "Records table with avatars, status badges, right-aligned amounts, sortable column, "
            "row actions and pagination; scrolls horizontally on phones. dense drops avatars for "
            "more rows; with_toolbar adds search, status filter, bulk selection and actions."
        ),
        capabilities=["table", "data", "dashboard", "list", "search", "filter", "sort"],
        supported_domains=_ALL,
        variants=["standard", "dense", "with_toolbar"],
        slots=[
            S(name="title", description="table title, e.g. Customers"),
            S(name="subtitle", description="one line on what the rows are"),
            S(name="columns", description="comma list of five column headers"),
            S(name="cta", description="primary action, e.g. Add customer"),
            S(name="secondary_cta", description="secondary action, e.g. Export"),
            S(name="filters", description="comma list of status filters, first is 'all'"),
            S(name="search_placeholder", description="search field placeholder"),
        ],
        implementation=_impl(
            "DataTable",
            ("Table", "shadcn"),
            ("Badge", "shadcn", "status"),
            ("Input", "shadcn", "search"),
            ("ToggleGroup", "radix", "status filter"),
            ("Checkbox", "native", "row selection"),
            ("Pagination", "shadcn"),
        ),
        animation_capabilities=["fade", "none"],
        responsive_behavior=ResponsiveBehavior(rules={"mobile": {"mode": "scroll"}}),
    ),
    ComponentDefinition(
        id="activity_feed",
        category=C.data,
        description=(
            "Chronological activity list. standard is a day-grouped timeline with avatars, "
            "status icons and inline comments; compact is a one-line-per-event list."
        ),
        capabilities=["activity", "dashboard", "timeline", "audit"],
        supported_domains=_ALL,
        variants=["standard", "compact"],
        slots=[
            S(name="title", description="panel title"),
            S(name="subtitle", description="one line under the title (standard)"),
            S(name="cta", description="link to the full log"),
            S(name="items", description="comma list of event sentences, replaces the samples"),
        ],
        implementation=_impl(
            "ActivityFeed", ("Avatar", "shadcn"), ("Card", "shadcn"), ("Timeline", "native")
        ),
        animation_capabilities=["fade", "fade_up", "stagger"],
    ),
    ComponentDefinition(
        id="progress_list",
        category=C.data,
        description=(
            "Goals with labelled progress: standard is a card of progress bars with value, "
            "percentage and status; cards is a grid of goal cards with progress rings."
        ),
        capabilities=["progress", "goals", "dashboard", "targets", "status"],
        supported_domains=_APP,
        variants=["standard", "cards"],
        slots=[
            S(name="title", description="panel title"),
            S(name="subtitle", description="one line under the title (standard)"),
            S(name="cta", description="action, e.g. New goal (standard)"),
            S(name="items", description="comma list of goal names"),
            S(name="values", description="comma list of percentages 0-100"),
            S(name="details", description="comma list of progress captions, e.g. 312 of 400"),
        ],
        implementation=_impl(
            "ProgressList",
            ("Card", "shadcn"),
            ("Progress", "native", "progressbar"),
            ("ProgressRing", "native", "inline SVG"),
            ("Badge", "shadcn", "status"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "reveal", "none"],
        responsive_behavior=_GRID_RULES,
    ),
    ComponentDefinition(
        id="notification_list",
        category=C.data,
        description=(
            "Inbox of notifications with unread markers, mark-as-read, archive and inline "
            "approve/decline actions. standard is a full panel with All/Unread/Mentions filter; "
            "compact is a popover-sized panel with a settings footer."
        ),
        capabilities=["notifications", "inbox", "dashboard", "actions", "unread"],
        supported_domains=_APP,
        variants=["standard", "compact"],
        slots=[
            S(name="title", description="panel title"),
            S(name="tabs", description="comma list of three filters: all, unread, mentions"),
            S(name="cta", description="mark-all action label"),
            S(name="secondary_cta", description="settings link (compact)"),
            S(name="footer_cta", description="view-all link (compact)"),
        ],
        implementation=_impl(
            "NotificationList",
            ("Card", "shadcn"),
            ("Avatar", "shadcn"),
            ("ToggleGroup", "radix", "filter"),
            ("Button", "shadcn", "row actions"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "none"],
    ),
    ComponentDefinition(
        id="empty_state",
        emits={"primary_cta": ["browse", "go_home"]},
        category=C.feedback,
        description=(
            "Empty state with illustration, title, body and primary action. standard is a "
            "centred illustrated panel; compact is an inline row for a card or table slot."
        ),
        capabilities=["empty_state", "onboarding", "feedback", "primary_cta"],
        supported_domains=_ALL,
        variants=["standard", "compact"],
        slots=[
            S(name="title", required=True),
            S(name="body"),
            S(name="primary_cta", required=True),
            S(name="secondary_cta", description="secondary link (standard)"),
        ],
        implementation=_impl(
            "EmptyState",
            ("Card", "shadcn"),
            ("Illustration", "native", "inline SVG"),
            ("Button", "shadcn", "primary"),
        ),
        animation_capabilities=["fade", "fade_up", "scale", "float", "none"],
        design_metadata=DesignMetadata(conversion_role="primary_cta"),
    ),
    ComponentDefinition(
        id="alert_banner",
        category=C.feedback,
        description=(
            "Inline alert with icon, title, body, actions and dismiss. info, success, warning "
            "and danger set tone and composition (danger lists issues, warning asks for action); "
            "banner is a one-line announcement bar whose tone comes from the tone slot."
        ),
        capabilities=["alert", "feedback", "status", "notice", "announcement", "dismissible"],
        supported_domains=_ALL,
        variants=["info", "success", "warning", "danger", "banner"],
        default_variant="info",
        slots=[
            S(name="title", required=True),
            S(name="body"),
            S(name="cta", description="primary action"),
            S(name="secondary_cta", description="secondary action"),
            S(name="tone", description="banner only: info|success|warning|danger"),
        ],
        implementation=_impl(
            "AlertBanner", ("Alert", "shadcn"), ("Button", "shadcn"), ("Icon", "lucide")
        ),
        animation_capabilities=["fade", "fade_down", "slide", "none"],
    ),
]
