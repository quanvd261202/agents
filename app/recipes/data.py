from app.layout.models import LayoutType as L
from app.recipes.models import RecipeDefinition
from app.recipes.models import RecipeSection as S

saas_landing = RecipeDefinition(
    id="saas_landing",
    page_type="landing",
    purpose="Convert visitors to signups for a SaaS product",
    domains=["saas", "*"],
    goals=["signup", "demo_request"],
    sections=[
        S(id="navigation", purpose="wayfinding + signup", component_types=["navigation"]),
        S(
            id="hero",
            purpose="value proposition + primary CTA",
            component_types=["hero"],
            layout=L.split_,
            goal="signup",
        ),
        S(
            id="social_proof",
            purpose="trust",
            component_types=["social_proof"],
            required=False,
            default_variant="logos",
        ),
        S(
            id="features",
            purpose="explain capabilities",
            component_types=["feature_bento"],
            layout=L.bento,
            reorderable=True,
            reorder_group="body",
        ),
        S(
            id="product_showcase",
            purpose="show the product",
            component_types=["product_showcase"],
            required=False,
            reorderable=True,
            reorder_group="body",
        ),
        S(
            id="metrics",
            purpose="proof by numbers",
            component_types=["metrics"],
            required=False,
            reorderable=True,
            reorder_group="body",
        ),
        S(
            id="testimonials",
            purpose="trust",
            component_types=["testimonial_grid"],
            required=False,
            layout=L.card_grid,
            reorderable=True,
            reorder_group="body",
        ),
        S(
            id="pricing",
            purpose="commit",
            component_types=["pricing_table"],
            required=False,
            goal="signup",
        ),
        S(id="faq", purpose="remove objections", component_types=["faq"], required=False),
        S(id="cta", purpose="final conversion", component_types=["cta"], goal="signup"),
        S(id="footer", purpose="secondary navigation", component_types=["footer"]),
    ],
    layout_rules={
        "hero_first": "hero must directly follow navigation",
        "cta_before_footer": "cta must be last body section",
    },
    responsive_rules={"mobile": "single column; bento collapses to stack; nav collapses to drawer"},
)

ecommerce_product = RecipeDefinition(
    id="ecommerce_product",
    page_type="product_detail",
    purpose="Help a shopper evaluate and buy a product",
    domains=["ecommerce"],
    goals=["add_to_cart"],
    sections=[
        S(id="navigation", purpose="wayfinding + cart", component_types=["navigation"]),
        S(
            id="breadcrumb",
            purpose="category context",
            component_types=["breadcrumb"],
            required=False,
        ),
        S(
            id="product_detail",
            purpose="evaluate + buy",
            component_types=["product_detail"],
            layout=L.split_,
            goal="add_to_cart",
        ),
        S(
            id="trust_signals",
            purpose="reduce purchase anxiety",
            component_types=["trust_signals"],
            required=False,
        ),
        S(
            id="product_features",
            purpose="details",
            component_types=["feature_bento", "faq"],
            required=False,
            layout=L.grid,
            reorderable=True,
            reorder_group="body",
        ),
        S(
            id="reviews",
            purpose="social proof",
            component_types=["reviews"],
            required=False,
            reorderable=True,
            reorder_group="body",
        ),
        S(
            id="related_products",
            purpose="cross-sell",
            component_types=["related_products"],
            required=False,
        ),
        S(
            id="recently_viewed",
            purpose="recovery",
            component_types=["related_products"],
            required=False,
            default_variant="grid",
        ),
        S(id="footer", purpose="secondary navigation", component_types=["footer"]),
    ],
    layout_rules={"detail_above_fold": "product_detail must be within first 3 sections"},
    responsive_rules={"mobile": "gallery above buy box; sticky add-to-cart"},
)

dashboard = RecipeDefinition(
    id="dashboard",
    page_type="dashboard",
    purpose="Monitor key metrics and act on them",
    domains=["saas", "dashboard", "admin"],
    goals=["monitor", "drill_down"],
    shell=L.sidebar,
    sections=[
        S(id="sidebar", purpose="app navigation", component_types=["dashboard_sidebar"]),
        S(id="page_header", purpose="context + actions", component_types=["page_header"]),
        S(id="stats", purpose="KPIs at a glance", component_types=["stats"], layout=L.grid),
        S(
            id="primary_visualization",
            purpose="main trend",
            component_types=["chart_panel"],
            layout=L.split_,
        ),
        S(
            id="secondary_content",
            purpose="detail table",
            component_types=["data_table", "chart_panel"],
            required=False,
            reorderable=True,
            reorder_group="body",
        ),
        S(
            id="activity",
            purpose="recent events",
            component_types=["activity_feed"],
            required=False,
            reorderable=True,
            reorder_group="body",
        ),
        S(
            id="footer",
            purpose="meta",
            component_types=["footer"],
            required=False,
            default_variant="minimal",
        ),
    ],
    layout_rules={"stats_first": "stats must directly follow page_header"},
    responsive_rules={"mobile": "sidebar becomes drawer; stats 1 column; table becomes cards"},
)

settings = RecipeDefinition(
    id="settings",
    page_type="settings",
    purpose="Let a user configure their account safely",
    domains=["saas", "dashboard", "admin"],
    goals=["update_settings"],
    shell=L.sidebar,
    sections=[
        S(id="sidebar", purpose="app navigation", component_types=["dashboard_sidebar"]),
        S(id="page_header", purpose="context", component_types=["page_header"]),
        S(
            id="settings_navigation",
            purpose="section switching",
            component_types=["settings_navigation"],
        ),
        S(
            id="settings_sections",
            purpose="the forms",
            component_types=["settings_form"],
            layout=L.stack,
        ),
        S(
            id="danger_zone",
            purpose="destructive actions, isolated",
            component_types=["danger_zone"],
        ),
    ],
    layout_rules={"danger_last": "danger_zone must be the final section"},
    responsive_rules={"mobile": "settings_navigation becomes tabs; forms full width"},
)

RECIPES: list[RecipeDefinition] = [saas_landing, ecommerce_product, dashboard, settings]
