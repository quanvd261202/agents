"""Marketing components. Implementation mappings live here, never in agents."""

from app.catalog.data._helpers import (  # noqa: F401
    _ALL,
    _CARD_ANIMS,
    _MEDIA,
    C,
    ComponentDefinition,
    DesignMetadata,
    ResponsiveBehavior,
    S,
    _impl,
)

COMPONENTS: list[ComponentDefinition] = [
    ComponentDefinition(
        id="hero",
        emits={
            "primary_cta": ["browse", "sign_up", "open_dashboard", "compare_plans", "contact"],
            "secondary_cta": ["learn_more", "compare_plans", "browse", "contact"],
        },
        category=C.marketing,
        description="Primary hero with headline, subhead, CTA and media",
        capabilities=["hero", "conversion", "headline", "responsive"],
        supported_layouts=["centered", "split", "full_bleed"],
        variants=[
            "standard",
            "split",
            "centered",
            "aurora",
            "video",
            "editorial",
            "fullbleed",
            "product_stack",
        ],
        slots=[
            S(name="eyebrow"),
            S(name="headline", required=True),
            S(name="subhead"),
            S(name="primary_cta"),
            S(name="secondary_cta"),
            S(name="media", description=_MEDIA),
            S(name="media_label"),
            S(name="badge"),
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
        description=(
            "Trust strip: a bordered grid of partner or press wordmarks (logos), a rating "
            "summary beside award badges (badges), or an endless scrolling logo band (marquee)"
        ),
        capabilities=["trust", "logos", "press", "awards", "rating"],
        supported_domains=_ALL,
        variants=["logos", "badges", "marquee"],
        default_variant="logos",
        slots=[
            S(name="eyebrow", description="Line above or beside the logos"),
            S(name="logos", description="Comma-separated partner, press or client names"),
            S(name="badges", description="badges variant: comma-separated 'Title|detail' awards"),
            S(name="rating", description="badges variant: average rating, e.g. '4.9'"),
            S(name="rating_label", description="badges variant: what the rating is based on"),
        ],
        implementation=_impl(
            "SocialProof",
            ("Marquee", "native", "scrolling band"),
            ("Rating", "native"),
            ("Icon", "lucide"),
        ),
        animation_capabilities=["none", "fade", "fade_up", "marquee"],
        design_metadata=DesignMetadata(
            visual_styles=["minimal", "premium", "editorial"], conversion_role="trust"
        ),
    ),
    ComponentDefinition(
        id="feature_bento",
        emits={"cta": ["learn_more", "browse"]},
        category=C.marketing,
        description=(
            "Bento grid of features with mixed tile sizes: a large media tile, a wide tile, "
            "a proof tile and icon tiles; compact is a heading beside a tight tile grid"
        ),
        capabilities=["features", "grid", "benefits", "responsive"],
        supported_domains=_ALL,
        supported_layouts=["bento", "grid", "asymmetric_grid"],
        variants=["standard", "premium", "compact"],
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="subtitle"),
            S(name="items", description="Comma-separated 'Title|Body' tiles, largest first"),
            S(name="media", description="the large tile: " + _MEDIA),
            S(name="stat", description="Proof tile number, e.g. '4.9'"),
            S(name="stat_label"),
            S(name="badge", description="premium variant: label on the large tile"),
            S(name="cta", description="standard variant: header link"),
        ],
        allowed_children=["feature_card"],
        implementation=_impl(
            "FeatureBento",
            ("Card", "native", "tile"),
            ("Media", "native"),
            ("Rating", "native"),
            ("Icon", "lucide"),
        ),
        animation_capabilities=_CARD_ANIMS,
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}}
        ),
        design_metadata=DesignMetadata(visual_styles=["premium", "modern", "bold"]),
    ),
    ComponentDefinition(
        id="feature_card",
        category=C.marketing,
        description=(
            "Single feature: icon tile, title and body (standard), centred icon medallion "
            "(icon_top), or copy beside an image (wide)"
        ),
        capabilities=["feature", "benefit"],
        supported_domains=_ALL,
        variants=["standard", "icon_top", "wide"],
        slots=[
            S(name="title", required=True),
            S(name="body"),
            S(
                name="icon",
                description=(
                    "sparkles, leaf, clock, gift, truck, package, heart, shield, star, palette, "
                    "layers, zap, globe, users, map, calendar, card, award"
                ),
            ),
        ],
        implementation=_impl(
            "FeatureCard", ("Card", "native"), ("Icon", "lucide"), ("Media", "native")
        ),
        animation_capabilities=_CARD_ANIMS,
        design_metadata=DesignMetadata(visual_styles=["minimal", "modern", "premium"]),
    ),
    ComponentDefinition(
        id="product_showcase",
        emits={"cta": ["sign_up", "browse", "learn_more"]},
        category=C.marketing,
        description=(
            "Large product or screen showcase: a staged image with callouts (standard), a "
            "website in a drawn browser window (browser_frame), or a phone with feature "
            "callouts either side (device_frame)"
        ),
        capabilities=["showcase", "media", "demo", "features"],
        supported_domains=_ALL,
        supported_layouts=["split", "centered"],
        variants=["standard", "browser_frame", "device_frame"],
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="subtitle"),
            S(name="media", description="the screen or image: " + _MEDIA),
            S(name="media_label"),
            S(
                name="points",
                description="Comma-separated 'Title|Body' callouts (3, or 6 for device)",
            ),
            S(name="cta", description="browser_frame variant: button label"),
            S(name="url", description="browser_frame variant: address bar text"),
            S(name="callout_label", description="standard variant: small label on the callout"),
            S(name="callout", description="standard variant: callout headline"),
            S(name="badge", description="standard variant: status pill on the image"),
        ],
        implementation=_impl(
            "ProductShowcase",
            ("BrowserFrame", "native"),
            ("DeviceFrame", "native"),
            ("Media", "native"),
            ("Icon", "lucide"),
        ),
        animation_capabilities=["fade", "fade_up", "scale", "parallax", "float"],
        design_metadata=DesignMetadata(visual_styles=["premium", "modern", "minimal"]),
    ),
    ComponentDefinition(
        id="metrics",
        category=C.marketing,
        description=(
            "Headline numbers: large ruled figures beside a heading (standard), a row of stat "
            "cards with an accent lead card (cards), or a compact divided band (inline)"
        ),
        capabilities=["stats", "trust", "numbers"],
        supported_domains=_ALL,
        variants=["standard", "cards", "inline"],
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="subtitle"),
            S(name="items", description="Comma-separated 'value|label' pairs, e.g. '38k|Orders'"),
        ],
        implementation=_impl("Metrics", ("Stat", "native"), ("Icon", "lucide")),
        animation_capabilities=["fade", "fade_up", "stagger", "number_ticker"],
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}}
        ),
        design_metadata=DesignMetadata(
            visual_styles=["minimal", "bold", "editorial"], conversion_role="trust"
        ),
    ),
    ComponentDefinition(
        id="testimonial_grid",
        category=C.marketing,
        description=(
            "Customer testimonials: a grid led by a featured quote (grid), a swipeable rail "
            "(carousel), or two opposing scrolling rows (marquee)"
        ),
        capabilities=["trust", "testimonials", "reviews"],
        supported_domains=_ALL,
        supported_layouts=["grid", "card_grid"],
        variants=["grid", "carousel", "marquee"],
        default_variant="grid",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="subtitle"),
            S(name="quotes", description="Comma-separated 'quote|name|role'; no commas inside"),
            S(name="rating_label", description="grid variant: review count beside the stars"),
        ],
        implementation=_impl(
            "Testimonials",
            ("Card", "native"),
            ("Avatar", "native"),
            ("Carousel", "embla"),
            ("Marquee", "native"),
            ("Rating", "native"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "marquee", "slide"],
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}}
        ),
        design_metadata=DesignMetadata(
            visual_styles=["premium", "editorial", "warm"], conversion_role="trust"
        ),
    ),
    ComponentDefinition(
        id="pricing_table",
        emits={"cta": ["sign_up", "checkout"]},
        category=C.marketing,
        description=(
            "Pricing tiers or membership plans with feature lists; highlighted raises the "
            "middle plan in an inverse card; toggle adds a working monthly/yearly switch"
        ),
        capabilities=["pricing", "plans", "membership", "conversion"],
        supported_domains=["saas", "*"],
        variants=["standard", "highlighted", "toggle"],
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="subtitle"),
            S(name="plans", description="Comma-separated plan names (3 recommended)"),
            S(name="prices", description="Comma-separated monthly prices, e.g. '$12,$29,$59'"),
            S(name="period", description="Price suffix, e.g. '/month'"),
            S(name="cta", description="Button prefix; the plan name follows"),
            S(name="badge", description="Label on the emphasised plan"),
            S(name="billing_note"),
            S(name="guarantee", description="standard variant: reassurance beside the heading"),
            S(name="yearly_discount", description="toggle variant: yearly saving in percent"),
            S(name="monthly_label"),
            S(name="yearly_label"),
            S(name="note", description="Footnote under the plans"),
        ],
        implementation=_impl(
            "PricingTable",
            ("Card", "native"),
            ("Badge", "native"),
            ("ToggleGroup", "radix", "billing period"),
            ("Button", "native", "cta"),
            ("Icon", "lucide"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "magnetic"],
        responsive_behavior=ResponsiveBehavior(rules={"mobile": {"columns": 1}}),
        design_metadata=DesignMetadata(
            visual_styles=["modern", "minimal", "premium"], conversion_role="primary_cta"
        ),
    ),
    ComponentDefinition(
        id="cta",
        emits={
            "primary_cta": ["browse", "sign_up", "compare_plans", "contact"],
            "secondary_cta": ["learn_more", "contact"],
        },
        category=C.marketing,
        description=(
            "Closing call to action: centred on a surface band (standard), a compact dark "
            "band (banner), an accent card with image (card), or a dark band with glow (gradient)"
        ),
        capabilities=["conversion", "cta"],
        supported_domains=_ALL,
        variants=["standard", "banner", "card", "gradient"],
        slots=[
            S(name="headline", required=True),
            S(name="body"),
            S(name="eyebrow"),
            S(name="primary_cta"),
            S(name="secondary_cta"),
            S(name="points", description="standard variant: comma-separated reassurances"),
            S(name="media", description="card variant: " + _MEDIA),
            S(name="media_label"),
        ],
        implementation=_impl("CTA", ("Button", "native", "cta"), ("Media", "native")),
        animation_capabilities=["fade", "fade_up", "glow", "magnetic"],
        design_metadata=DesignMetadata(
            visual_styles=["bold", "premium", "minimal"], conversion_role="primary_cta"
        ),
    ),
    ComponentDefinition(
        id="cta_split",
        emits={
            "primary_cta": ["browse", "sign_up", "compare_plans", "contact"],
            "secondary_cta": ["learn_more", "contact"],
        },
        category=C.marketing,
        description=(
            "Two-column call to action: copy and buttons beside an image with a status panel "
            "(media), or two offers side by side, one in an inverse card (offers)"
        ),
        capabilities=["conversion", "cta", "visit", "choice"],
        supported_domains=_ALL,
        supported_layouts=["split"],
        variants=["media", "offers"],
        default_variant="media",
        slots=[
            S(name="headline", required=True),
            S(name="body"),
            S(name="eyebrow"),
            S(name="primary_cta"),
            S(name="secondary_cta"),
            S(name="note", description="media variant: small line under the buttons"),
            S(name="media", description="media variant: " + _MEDIA),
            S(name="media_label"),
            S(name="badge_label", description="media variant: label on the image panel"),
            S(name="badge", description="media variant: value on the image panel"),
            S(name="offers", description="offers variant: two 'tag|title|body|button' entries"),
        ],
        implementation=_impl(
            "CTASplit", ("Button", "native", "cta"), ("Media", "native"), ("Icon", "lucide")
        ),
        animation_capabilities=["fade", "fade_up", "reveal", "stagger"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "modern", "editorial"], conversion_role="primary_cta"
        ),
    ),
    ComponentDefinition(
        id="integrations_grid",
        category=C.marketing,
        description=(
            "Grid of connected apps and services with names and categories: filterable tiles "
            "(grid) or lists grouped under category headings (grouped)"
        ),
        capabilities=["integrations", "ecosystem", "grid", "filter"],
        supported_domains=_ALL,
        supported_layouts=["grid"],
        variants=["grid", "grouped"],
        default_variant="grid",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="subtitle"),
            S(name="items", description="Comma-separated 'Name|Category|what it does' entries"),
            S(name="all_label", description="grid variant: label of the unfiltered chip"),
            S(name="cta"),
        ],
        implementation=_impl(
            "IntegrationsGrid",
            ("ToggleGroup", "radix", "category filter"),
            ("Card", "native", "tile"),
            ("Icon", "lucide"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "scale"],
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}}
        ),
        design_metadata=DesignMetadata(
            visual_styles=["modern", "minimal"], conversion_role="trust"
        ),
    ),
    ComponentDefinition(
        id="app_download",
        category=C.marketing,
        description=(
            "Mobile app promotion with drawn phones, store buttons, benefits, QR and rating "
            "(standard), or a dark band with a phone rising from its edge (banner)"
        ),
        capabilities=["app", "download", "conversion", "mobile"],
        supported_domains=_ALL,
        supported_layouts=["split"],
        variants=["standard", "banner"],
        slots=[
            S(name="headline", required=True),
            S(name="body"),
            S(name="eyebrow"),
            S(name="points", description="standard variant: comma-separated app benefits"),
            S(name="media", description="the app screen: " + _MEDIA),
            S(name="media_label"),
            S(name="qr_label"),
            S(name="rating", description="standard variant: store rating, e.g. '4.8'"),
            S(name="rating_label"),
        ],
        implementation=_impl(
            "AppDownload",
            ("DeviceFrame", "native"),
            ("Media", "native"),
            ("Button", "native", "store"),
            ("Icon", "lucide"),
        ),
        animation_capabilities=["fade", "fade_up", "float", "parallax"],
        design_metadata=DesignMetadata(
            visual_styles=["modern", "premium", "bold"], conversion_role="primary_cta"
        ),
    ),
]
