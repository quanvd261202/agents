"""Structure components. Implementation mappings live here, never in agents."""

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

COMPONENTS: list[ComponentDefinition] = [
    ComponentDefinition(
        id="navigation",
        emits={
            "nav": ["*"],
            "logo": ["go_home"],
            "cart": ["view_cart"],
            "account": ["sign_in", "open_dashboard", "open_settings"],
            "cta": ["sign_up", "browse", "compare_plans", "contact"],
        },
        category=C.navigation,
        description=(
            "Top navigation bar: logo, links, actions (search, account, cart with count, CTA) "
            "and a mobile sheet menu"
        ),
        capabilities=["navigation", "branding", "responsive", "sticky", "mobile_menu", "cart"],
        supported_domains=_ALL,
        variants=["standard", "transparent", "minimal", "centered"],
        default_variant="standard",
        slots=[
            S(name="logo", description="Brand name shown as the wordmark"),
            S(name="links", description="Comma-separated nav links, e.g. 'Shop,Journal,About'"),
            S(
                name="actions",
                description=(
                    "Comma-separated actions. 'Search', 'Sign in'/'Account' and 'Cart' become "
                    "icon or ghost controls; the last other label is the primary button"
                ),
            ),
            S(name="cart_count", description="Items in the cart badge, e.g. '2'"),
        ],
        implementation=_impl(
            "NavBar",
            ("nav", "native", "links"),
            ("Button", "native", "cta"),
            ("Dialog", "radix", "mobile_menu"),
            ("ShoppingBag", "lucide", "cart"),
            ("Menu", "lucide", "menu_toggle"),
        ),
        animation_capabilities=["fade", "fade_down", "none"],
        responsive_behavior=ResponsiveBehavior(rules={"mobile": {"links": "collapse"}}),
        design_metadata=DesignMetadata(visual_styles=["premium", "minimal", "editorial"]),
    ),
    ComponentDefinition(
        id="dashboard_sidebar",
        category=C.navigation,
        description=(
            "App sidebar: workspace switcher, search, grouped nav with counts, usage card and "
            "user; icon rail on tablet, drawer on phones"
        ),
        capabilities=["navigation", "app_shell", "collapsible", "responsive"],
        supported_domains=["saas", "dashboard", "admin"],
        variants=["standard", "compact", "floating"],
        default_variant="standard",
        slots=[
            S(name="logo", description="Workspace or brand name"),
            S(name="workspace", description="Line under the name, e.g. 'Flagship · Pro plan'"),
            S(name="items", description="Comma-separated main items; 'Orders (12)' adds a count"),
            S(
                name="secondary_items",
                description="Comma-separated lower items, e.g. 'Settings,Help'",
            ),
            S(name="active", description="Label of the current item"),
            S(name="user_name"),
            S(name="user_role"),
            S(name="usage_title", description="Usage card heading, e.g. 'Monthly orders'"),
            S(name="usage_body", description="Usage card detail line"),
        ],
        implementation=_impl(
            "Sidebar",
            ("aside", "native"),
            ("Tooltip", "radix", "rail_labels"),
            ("Dialog", "radix", "mobile_drawer"),
            ("Icons", "lucide", "nav_icons"),
        ),
        animation_capabilities=["fade", "slide", "none"],
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"mode": "drawer"}, "tablet": {"mode": "collapsed"}}
        ),
        design_metadata=DesignMetadata(visual_styles=["premium", "minimal"]),
    ),
    ComponentDefinition(
        id="breadcrumb",
        emits={"trail": ["*"]},
        category=C.navigation,
        description="Breadcrumb trail; long trails collapse behind an ellipsis on phones",
        capabilities=["navigation", "wayfinding"],
        supported_domains=_ALL,
        variants=["standard", "compact"],
        default_variant="standard",
        slots=[
            S(
                name="items",
                description="Comma-separated trail, last item is the current page, e.g. "
                "'Home,Shop,Tea,Garden Reserve'",
            ),
        ],
        implementation=_impl(
            "Breadcrumb", ("nav", "native"), ("ChevronRight", "lucide", "separator")
        ),
        animation_capabilities=["fade", "none"],
    ),
    ComponentDefinition(
        id="page_header",
        category=C.structure,
        description=(
            "App page header: breadcrumb, title with status, description, meta line and "
            "actions; with_tabs adds sub-navigation"
        ),
        capabilities=["hierarchy", "actions", "wayfinding"],
        supported_domains=_ALL,
        variants=["standard", "with_tabs", "compact"],
        default_variant="standard",
        slots=[
            S(name="title", required=True),
            S(name="description"),
            S(
                name="actions",
                description="Comma-separated actions; the last is primary, e.g. 'Export,New order'",
            ),
            S(name="breadcrumb", description="Comma-separated trail above the title"),
            S(name="status", description="Status pill next to the title, e.g. 'Live'"),
            S(
                name="meta",
                description="Comma-separated meta line, e.g. 'Last 30 days,Updated now'",
            ),
            S(
                name="tabs",
                description="Comma-separated tabs (with_tabs); 'Sales (24)' adds a count",
            ),
        ],
        implementation=_impl(
            "PageHeader",
            ("Heading", "native"),
            ("Button", "native", "action"),
            ("Icons", "lucide", "action_icons"),
        ),
        animation_capabilities=["fade", "fade_up", "none"],
    ),
    ComponentDefinition(
        id="footer",
        emits={"nav": ["*"], "logo": ["go_home"]},
        category=C.structure,
        description=(
            "Site footer: standard link columns, minimal single line, or mega with newsletter, "
            "columns, contact and social"
        ),
        capabilities=["navigation", "legal", "newsletter", "social"],
        supported_domains=_ALL,
        variants=["standard", "minimal", "mega"],
        default_variant="standard",
        slots=[
            S(name="logo"),
            S(name="tagline", description="One line about the brand"),
            S(
                name="columns",
                description="Comma-separated column headings, e.g. 'Shop,About,Help'",
            ),
            S(name="legal", description="Copyright line"),
            S(name="social", description="Comma-separated networks, e.g. 'Instagram,Pinterest'"),
            S(name="contact", description="Address and email (mega)"),
            S(name="newsletter_eyebrow"),
            S(name="newsletter_title"),
            S(name="newsletter_body"),
            S(name="newsletter_cta"),
        ],
        implementation=_impl(
            "Footer",
            ("footer", "native"),
            ("Input", "native", "newsletter"),
            ("Button", "native", "subscribe"),
            ("Globe", "lucide", "locale"),
        ),
        animation_capabilities=["fade", "fade_up", "none"],
    ),
    ComponentDefinition(
        id="announcement_bar",
        emits={"link_label": ["browse", "compare_plans", "learn_more"]},
        category=C.structure,
        description="Thin dismissible promo or notice strip above the navigation",
        capabilities=["announcement", "promotion", "dismissible"],
        supported_domains=_ALL,
        variants=["standard", "accent", "marquee"],
        default_variant="standard",
        slots=[
            S(name="message", description="The notice, one short sentence"),
            S(name="link_label", description="Inline link after the message"),
            S(name="badge", description="Pill before the message (accent), e.g. 'New'"),
            S(name="messages", description="Comma-separated rotating messages (marquee)"),
        ],
        implementation=_impl(
            "AnnouncementBar",
            ("div", "native"),
            ("Button", "native", "dismiss"),
            ("X", "lucide", "dismiss_icon"),
        ),
        animation_capabilities=["fade", "fade_down", "marquee", "none"],
        design_metadata=DesignMetadata(conversion_role="promotion"),
    ),
    ComponentDefinition(
        id="category_nav",
        emits={"cta": ["browse"]},
        category=C.navigation,
        description="Horizontal category navigation with active state; scrolls sideways on phones",
        capabilities=["navigation", "browse", "filter", "responsive"],
        supported_domains=_ALL,
        variants=["standard", "pills", "visual"],
        default_variant="standard",
        slots=[
            S(name="items", description="Comma-separated categories; 'Tea (12)' adds a count"),
            S(name="active", description="Label of the active category"),
            S(name="label", description="Accessible name, e.g. 'Categories'"),
            S(name="cta", description="Trailing link (standard), e.g. 'View all'"),
        ],
        implementation=_impl(
            "CategoryNav",
            ("nav", "native"),
            ("Media", "native", "thumbnails"),
            ("SlidersHorizontal", "lucide", "filters"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "none"],
    ),
    ComponentDefinition(
        id="pagination",
        category=C.navigation,
        description="Page navigation: numbered with prev/next, compact page counter, or load more",
        capabilities=["navigation", "browse", "pagination"],
        supported_domains=_ALL,
        variants=["standard", "compact", "load_more"],
        default_variant="standard",
        slots=[
            S(name="total_pages", description="Number of pages, e.g. '12'"),
            S(name="current_page", description="Current page, e.g. '3'"),
            S(name="per_page", description="Items per page, e.g. '24'"),
            S(name="total_items", description="Total items, e.g. '286'"),
            S(name="item_label", description="Plural noun for the items, e.g. 'products'"),
            S(name="cta", description="Load more button label"),
        ],
        implementation=_impl(
            "Pagination",
            ("nav", "native"),
            ("Button", "native", "pages"),
            ("ChevronLeft", "lucide", "prev_next"),
        ),
        animation_capabilities=["fade", "none"],
    ),
    ComponentDefinition(
        id="section_header",
        emits={"cta": ["browse", "learn_more"]},
        category=C.structure,
        description="Standalone eyebrow, title, body and action that opens a group of sections",
        capabilities=["hierarchy", "wayfinding", "storytelling"],
        supported_domains=_ALL,
        variants=["standard", "centered", "split"],
        default_variant="standard",
        slots=[
            S(name="eyebrow"),
            S(name="title", description="Section group heading (h2)"),
            S(name="body"),
            S(name="cta"),
            S(name="secondary_cta", description="Second button (centered)"),
            S(name="index", description="Counter on the rule (split), e.g. '01 / 04'"),
        ],
        implementation=_impl(
            "SectionHeaderBlock", ("Heading", "native"), ("Button", "native", "action")
        ),
        animation_capabilities=["fade", "fade_up", "reveal", "none"],
    ),
    ComponentDefinition(
        id="sticky_cta_bar",
        emits={"cta": ["add_to_cart", "checkout", "sign_up", "browse"], "promo_cta": ["browse"]},
        category=C.structure,
        description=(
            "Sticky bar with a short summary and the primary CTA: docked purchase bar, floating "
            "pill, or promo band"
        ),
        capabilities=["conversion", "sticky", "commerce", "promotion"],
        supported_domains=_ALL,
        variants=["standard", "floating", "promo"],
        default_variant="standard",
        slots=[
            S(name="title", description="Product or offer name"),
            S(name="summary", description="One-line detail, e.g. '250 g · Whole bean'"),
            S(name="price"),
            S(name="price_note", description="Line under the price (standard)"),
            S(name="cta", description="Primary action, e.g. 'Add to bag'"),
            S(name="secondary_cta"),
            S(name="promo_title", description="Headline (promo)"),
            S(name="promo_body", description="Detail line (promo)"),
            S(name="promo_cta", description="Primary action (promo)"),
        ],
        implementation=_impl(
            "StickyCtaBar",
            ("section", "native", "sticky"),
            ("Button", "native", "cta"),
            ("Media", "native", "thumbnail"),
        ),
        animation_capabilities=["fade", "fade_up", "slide", "none"],
        design_metadata=DesignMetadata(conversion_role="primary_cta"),
    ),
]
