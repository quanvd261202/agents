"""Seed semantic component catalog. Implementation mappings live here, never in agents."""

from app.catalog.models import (
    ComponentCategory as C,
)
from app.catalog.models import (
    ComponentDefinition,
    DesignMetadata,
    ImplementationMapping,
    ResponsiveBehavior,
)
from app.catalog.models import (
    ImplementationPart as P,
)
from app.catalog.models import (
    SlotDefinition as S,
)

_ALL = ["*"]
_CARD_ANIMS = ["fade", "fade_up", "scale", "stagger", "reveal"]


def _impl(
    root: str, *parts: tuple[str, str] | tuple[str, str, str], **props: str | int | bool
) -> ImplementationMapping:
    return ImplementationMapping(
        root=root,
        parts=[P(name=p[0], library=p[1], role=p[2] if len(p) > 2 else "") for p in parts],
        default_props=props,
    )


COMPONENTS: list[ComponentDefinition] = [
    # --- structure / navigation -----------------------------------------------------------
    ComponentDefinition(
        id="navigation",
        category=C.navigation,
        description="Top navigation bar with logo, links and actions",
        capabilities=["navigation", "branding", "responsive", "sticky"],
        variants=["standard", "transparent", "minimal", "centered"],
        slots=[S(name="logo"), S(name="links"), S(name="actions")],
        implementation=_impl(
            "NavBar",
            ("NavigationMenu", "shadcn"),
            ("Button", "shadcn", "cta"),
            ("Sheet", "shadcn", "mobile_menu"),
        ),
        animation_capabilities=["fade", "fade_down", "none"],
        responsive_behavior=ResponsiveBehavior(rules={"mobile": {"links": "collapse"}}),
    ),
    ComponentDefinition(
        id="dashboard_sidebar",
        category=C.navigation,
        description="Vertical app sidebar with grouped nav items",
        capabilities=["navigation", "app_shell", "collapsible"],
        supported_domains=["saas", "dashboard", "admin"],
        variants=["standard", "compact", "floating"],
        implementation=_impl("Sidebar", ("Sidebar", "shadcn"), ("Tooltip", "radix")),
        animation_capabilities=["fade", "slide", "none"],
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"mode": "drawer"}, "tablet": {"mode": "collapsed"}}
        ),
    ),
    ComponentDefinition(
        id="breadcrumb",
        category=C.navigation,
        description="Breadcrumb trail",
        capabilities=["navigation", "wayfinding"],
        variants=["standard", "compact"],
        implementation=_impl("Breadcrumb", ("Breadcrumb", "shadcn")),
        animation_capabilities=["fade", "none"],
    ),
    ComponentDefinition(
        id="page_header",
        category=C.structure,
        description="Page title, description and primary actions",
        capabilities=["hierarchy", "actions"],
        variants=["standard", "with_tabs", "compact"],
        slots=[S(name="title", required=True), S(name="description"), S(name="actions")],
        implementation=_impl("PageHeader", ("Heading", "native"), ("Button", "shadcn", "action")),
        animation_capabilities=["fade", "fade_up", "none"],
    ),
    ComponentDefinition(
        id="footer",
        category=C.structure,
        description="Site footer with link columns and legal",
        capabilities=["navigation", "legal"],
        variants=["standard", "minimal", "mega"],
        implementation=_impl("Footer", ("Separator", "shadcn")),
        animation_capabilities=["fade", "none"],
    ),
    # --- marketing -------------------------------------------------------------------------
    ComponentDefinition(
        id="hero",
        category=C.marketing,
        description="Primary hero with headline, subhead, CTA and media",
        capabilities=["hero", "conversion", "headline", "responsive"],
        supported_layouts=["centered", "split", "full_bleed"],
        variants=["standard", "split", "centered", "aurora", "video"],
        slots=[
            S(name="headline", required=True),
            S(name="subhead"),
            S(name="primary_cta"),
            S(name="secondary_cta"),
            S(name="media"),
        ],
        implementation=_impl(
            "Hero",
            ("Button", "shadcn", "cta"),
            ("AuroraBackground", "aceternity", "bg"),
            ("motion.div", "motion"),
        ),
        animation_capabilities=["fade", "fade_up", "reveal", "stagger", "parallax", "glow"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "modern", "minimal", "bold"], conversion_role="primary_cta"
        ),
    ),
    ComponentDefinition(
        id="social_proof",
        category=C.marketing,
        description="Logo strip or trust badges",
        capabilities=["trust", "logos"],
        variants=["logos", "badges", "marquee"],
        implementation=_impl("SocialProof", ("Marquee", "magicui")),
        animation_capabilities=["fade", "marquee", "none"],
        design_metadata=DesignMetadata(conversion_role="trust"),
    ),
    ComponentDefinition(
        id="feature_bento",
        category=C.marketing,
        description="Bento grid of feature cards",
        capabilities=["features", "grid", "responsive"],
        supported_layouts=["bento", "grid", "asymmetric_grid"],
        variants=["standard", "premium", "compact"],
        allowed_children=["feature_card"],
        implementation=_impl("FeatureBento", ("BentoGrid", "magicui"), ("Card", "shadcn")),
        animation_capabilities=_CARD_ANIMS,
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}}
        ),
    ),
    ComponentDefinition(
        id="feature_card",
        category=C.marketing,
        description="Single feature card with icon, title, body",
        capabilities=["feature"],
        variants=["standard", "icon_top", "wide"],
        slots=[S(name="title", required=True), S(name="body"), S(name="icon")],
        implementation=_impl("FeatureCard", ("Card", "shadcn"), ("Icon", "native")),
        animation_capabilities=_CARD_ANIMS,
    ),
    ComponentDefinition(
        id="product_showcase",
        category=C.marketing,
        description="Large product screenshot or demo",
        capabilities=["showcase", "media"],
        variants=["standard", "browser_frame", "device_frame"],
        implementation=_impl("ProductShowcase", ("Safari", "magicui"), ("motion.div", "motion")),
        animation_capabilities=["fade", "fade_up", "scale", "parallax", "float"],
    ),
    ComponentDefinition(
        id="metrics",
        category=C.marketing,
        description="Row of headline numbers",
        capabilities=["stats", "trust"],
        variants=["standard", "cards", "inline"],
        implementation=_impl("Metrics", ("NumberTicker", "magicui")),
        animation_capabilities=["fade", "number_ticker", "stagger"],
    ),
    ComponentDefinition(
        id="testimonial_grid",
        category=C.marketing,
        description="Customer testimonials",
        capabilities=["trust", "testimonials"],
        supported_layouts=["grid", "card_grid"],
        variants=["grid", "carousel", "marquee"],
        implementation=_impl(
            "Testimonials", ("Card", "shadcn"), ("Avatar", "shadcn"), ("Marquee", "magicui")
        ),
        animation_capabilities=["fade", "stagger", "marquee"],
        design_metadata=DesignMetadata(conversion_role="trust"),
    ),
    ComponentDefinition(
        id="pricing_table",
        category=C.marketing,
        description="Pricing tiers with feature comparison",
        capabilities=["pricing", "conversion"],
        supported_domains=["saas", "*"],
        variants=["standard", "highlighted", "toggle"],
        implementation=_impl(
            "PricingTable",
            ("Card", "shadcn"),
            ("Badge", "shadcn"),
            ("Switch", "shadcn"),
            ("Button", "shadcn", "cta"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "magnetic"],
        responsive_behavior=ResponsiveBehavior(rules={"mobile": {"columns": 1}}),
        design_metadata=DesignMetadata(conversion_role="primary_cta"),
    ),
    ComponentDefinition(
        id="faq",
        category=C.content,
        description="Accordion of frequently asked questions",
        capabilities=["faq", "support"],
        variants=["standard", "two_column"],
        implementation=_impl("FAQ", ("Accordion", "shadcn")),
        animation_capabilities=["fade", "fade_up", "none"],
    ),
    ComponentDefinition(
        id="cta",
        category=C.marketing,
        description="Closing call to action band",
        capabilities=["conversion", "cta"],
        variants=["standard", "banner", "card", "gradient"],
        slots=[S(name="headline", required=True), S(name="primary_cta")],
        implementation=_impl("CTA", ("Button", "shadcn", "cta"), ("ShimmerButton", "magicui")),
        animation_capabilities=["fade", "fade_up", "glow", "magnetic"],
        design_metadata=DesignMetadata(conversion_role="primary_cta"),
    ),
    # --- commerce ---------------------------------------------------------------------------
    ComponentDefinition(
        id="product_card",
        category=C.commerce,
        description="Product summary card with image, price, action",
        capabilities=["product_summary", "commerce", "responsive"],
        supported_domains=["ecommerce"],
        variants=["standard", "premium", "compact"],
        slots=[
            S(name="image", required=True),
            S(name="title", required=True),
            S(name="price", required=True),
            S(name="badge"),
        ],
        implementation=_impl(
            "ProductCard",
            ("Card", "shadcn"),
            ("Image", "native"),
            ("Badge", "shadcn"),
            ("Button", "shadcn", "add_to_cart"),
            ("motion.div", "motion"),
        ),
        animation_capabilities=_CARD_ANIMS,
    ),
    ComponentDefinition(
        id="product_grid",
        category=C.commerce,
        description="Responsive grid of product cards",
        capabilities=["commerce", "browse", "grid", "responsive"],
        supported_domains=["ecommerce"],
        supported_layouts=["grid", "card_grid"],
        variants=["standard", "premium", "dense"],
        allowed_children=["product_card"],
        implementation=_impl("ProductGrid", ("Grid", "native")),
        animation_capabilities=["fade", "stagger", "none"],
        responsive_behavior=ResponsiveBehavior(
            rules={
                "mobile": {"columns": 1},
                "tablet": {"columns": 2},
                "desktop": {"columns": 3},
                "wide": {"columns": 4},
            }
        ),
    ),
    ComponentDefinition(
        id="product_detail",
        category=C.commerce,
        description="Gallery, title, price, variants, add to cart",
        capabilities=["commerce", "product_evaluation", "conversion"],
        supported_domains=["ecommerce"],
        supported_layouts=["split", "media_text"],
        variants=["standard", "premium_split", "stacked"],
        implementation=_impl(
            "ProductDetail",
            ("Carousel", "shadcn"),
            ("RadioGroup", "shadcn", "variants"),
            ("Button", "shadcn", "add_to_cart"),
            ("Tabs", "shadcn"),
        ),
        animation_capabilities=["fade", "fade_up", "reveal", "stagger"],
        design_metadata=DesignMetadata(conversion_role="primary_cta"),
    ),
    ComponentDefinition(
        id="trust_signals",
        category=C.commerce,
        description="Shipping, returns, secure checkout badges",
        capabilities=["trust", "commerce"],
        variants=["standard", "inline"],
        implementation=_impl("TrustSignals", ("Icon", "native")),
        animation_capabilities=["fade", "none"],
        design_metadata=DesignMetadata(conversion_role="trust"),
    ),
    ComponentDefinition(
        id="reviews",
        category=C.commerce,
        description="Rating summary and review list",
        capabilities=["trust", "reviews", "commerce"],
        variants=["standard", "compact"],
        implementation=_impl("Reviews", ("Progress", "shadcn"), ("Avatar", "shadcn")),
        animation_capabilities=["fade", "stagger"],
    ),
    ComponentDefinition(
        id="related_products",
        category=C.commerce,
        description="Carousel of related products",
        capabilities=["commerce", "cross_sell"],
        supported_domains=["ecommerce"],
        variants=["carousel", "grid"],
        allowed_children=["product_card"],
        implementation=_impl("RelatedProducts", ("Carousel", "shadcn")),
        animation_capabilities=["fade", "stagger"],
    ),
    # --- data / app -------------------------------------------------------------------------
    ComponentDefinition(
        id="stats",
        category=C.data,
        description="KPI stat cards",
        capabilities=["stats", "dashboard", "analytics"],
        supported_domains=["saas", "dashboard", "admin"],
        variants=["standard", "with_trend", "compact"],
        implementation=_impl(
            "Stats", ("Card", "shadcn"), ("NumberTicker", "magicui"), ("Sparkline", "native")
        ),
        animation_capabilities=["fade", "number_ticker", "stagger"],
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}, "desktop": {"columns": 4}}
        ),
    ),
    ComponentDefinition(
        id="chart_panel",
        category=C.data,
        description="Primary visualization card",
        capabilities=["analytics", "charts", "dashboard"],
        supported_domains=["saas", "dashboard", "admin"],
        variants=["line", "bar", "area", "donut"],
        implementation=_impl("ChartPanel", ("Card", "shadcn"), ("Chart", "shadcn")),
        animation_capabilities=["fade", "reveal", "none"],
    ),
    ComponentDefinition(
        id="data_table",
        category=C.data,
        description="Sortable, filterable data table",
        capabilities=["table", "data", "dashboard"],
        variants=["standard", "dense", "with_toolbar"],
        implementation=_impl(
            "DataTable", ("Table", "shadcn"), ("DropdownMenu", "shadcn"), ("Pagination", "shadcn")
        ),
        animation_capabilities=["fade", "none"],
        responsive_behavior=ResponsiveBehavior(rules={"mobile": {"mode": "cards"}}),
    ),
    ComponentDefinition(
        id="activity_feed",
        category=C.data,
        description="Chronological activity list",
        capabilities=["activity", "dashboard", "timeline"],
        variants=["standard", "compact"],
        implementation=_impl("ActivityFeed", ("Avatar", "shadcn"), ("ScrollArea", "shadcn")),
        animation_capabilities=["fade", "stagger"],
    ),
    # --- forms ------------------------------------------------------------------------------
    ComponentDefinition(
        id="settings_navigation",
        category=C.forms,
        description="Secondary nav between settings sections",
        capabilities=["navigation", "settings"],
        variants=["tabs", "vertical"],
        implementation=_impl("SettingsNav", ("Tabs", "shadcn")),
        animation_capabilities=["fade", "none"],
    ),
    ComponentDefinition(
        id="settings_form",
        category=C.forms,
        description="Grouped settings form section with save action",
        capabilities=["settings", "form"],
        variants=["standard", "card", "inline"],
        slots=[S(name="title", required=True), S(name="description")],
        implementation=_impl(
            "SettingsForm",
            ("Form", "shadcn"),
            ("Input", "shadcn"),
            ("Switch", "shadcn"),
            ("Select", "shadcn"),
            ("Button", "shadcn", "save"),
        ),
        animation_capabilities=["fade", "none"],
    ),
    ComponentDefinition(
        id="danger_zone",
        category=C.forms,
        description="Destructive actions section",
        capabilities=["settings", "destructive"],
        variants=["standard"],
        implementation=_impl(
            "DangerZone",
            ("Card", "shadcn"),
            ("AlertDialog", "shadcn"),
            ("Button", "shadcn", "destructive"),
        ),
        animation_capabilities=["fade", "none"],
    ),
]


def default_component_registry():  # type: ignore[no-untyped-def]
    from app.catalog.registry import ComponentRegistry

    return ComponentRegistry(COMPONENTS)
