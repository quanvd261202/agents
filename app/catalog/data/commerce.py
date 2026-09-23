"""Commerce components. Implementation mappings live here, never in agents."""

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

_SHOP = ["ecommerce"]
_MEDIA = "what the image shows: cup, bag, leaf, glass, product, space..."
_LIST = "comma-separated"
_OPTIONS = "comma-separated options; the single value 'hide' removes the group"
_PRICES = "comma-separated price deltas matching the options, e.g. 0,0.60,1.10"


def _grid(desktop: int, wide: int | None = None) -> ResponsiveBehavior:
    rules: dict[str, dict[str, str | int]] = {
        "mobile": {"columns": 1},
        "tablet": {"columns": 2},
        "desktop": {"columns": desktop},
    }
    if wide:
        rules["wide"] = {"columns": wide}
    return ResponsiveBehavior(rules=rules)


def _header_slots(*extra: str) -> list[S]:
    return [S(name="eyebrow"), S(name="title"), S(name="subtitle"), *(S(name=e) for e in extra)]


COMPONENTS: list[ComponentDefinition] = [
    ComponentDefinition(
        id="product_card",
        category=C.commerce,
        description="Product summary card with image, price, action",
        capabilities=["product_summary", "commerce", "responsive"],
        supported_domains=_SHOP,
        variants=["standard", "premium", "compact"],
        slots=[
            S(name="image", required=True),
            S(name="title", required=True),
            S(name="note"),
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
        description="Responsive grid of product cards with a section header and view-all link",
        capabilities=["commerce", "browse", "grid", "responsive"],
        supported_domains=_SHOP,
        supported_layouts=["grid", "card_grid"],
        variants=["standard", "premium", "dense"],
        slots=_header_slots("cta"),
        allowed_children=["product_card"],
        implementation=_impl("ProductGrid", ("Grid", "native"), ("Button", "shadcn", "view_all")),
        animation_capabilities=["fade", "stagger", "none"],
        responsive_behavior=_grid(3, 4),
    ),
    ComponentDefinition(
        id="product_detail",
        category=C.commerce,
        description=(
            "Product page lead: gallery with thumbnails, name, price, rating, size / temperature / "
            "milk / sweetness choices, quantity, add to cart, favourite and product details. "
            "standard = gallery + sticky buy box with tabs; premium_split = side-rail gallery and "
            "panel with highlights and accordion; stacked = centred title, image carousel, options "
            "card beside tabs"
        ),
        capabilities=["commerce", "product_evaluation", "conversion", "customization", "gallery"],
        supported_domains=_SHOP,
        supported_layouts=["split", "media_text"],
        variants=["standard", "premium_split", "stacked"],
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="description"),
            S(name="price"),
            S(name="compare_at", description="original price, shown struck through"),
            S(name="rating", description="e.g. 4.8"),
            S(name="review_count"),
            S(name="badge"),
            S(name="media", description=_MEDIA),
            S(name="sizes", description=_OPTIONS),
            S(name="temperatures", description=_OPTIONS),
            S(name="milks", description=_OPTIONS),
            S(name="sweetness", description=_OPTIONS),
            S(name="size_label"),
            S(name="temperature_label"),
            S(name="milk_label"),
            S(name="sweetness_label"),
            S(name="primary_cta"),
            S(name="shipping_note"),
            S(name="returns_note"),
            S(name="highlights", description="three short product highlights (premium_split)"),
            S(name="details"),
            S(name="specs", description="comma-separated 'Label: value' pairs"),
            S(name="notes", description="comma-separated character / tasting notes"),
            S(name="shipping"),
            S(name="details_label"),
            S(name="notes_label"),
            S(name="shipping_label"),
        ],
        implementation=_impl(
            "ProductDetail",
            ("Carousel", "embla", "gallery"),
            ("ToggleGroup", "radix", "variants"),
            ("QuantityStepper", "native", "quantity"),
            ("Button", "shadcn", "add_to_cart"),
            ("Tabs", "radix", "details"),
            ("Accordion", "radix", "details"),
        ),
        animation_capabilities=["fade", "fade_up", "reveal", "stagger"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "modern", "minimal"], conversion_role="primary_cta"
        ),
    ),
    ComponentDefinition(
        id="trust_signals",
        category=C.commerce,
        description="Shipping, returns and secure checkout badges with icons (row, strip or cards)",
        capabilities=["trust", "commerce", "reassurance"],
        variants=["standard", "inline", "cards"],
        slots=[
            S(name="title", description="accessible name of the band"),
            S(name="items", description="comma-separated short promises"),
            S(name="details", description="comma-separated supporting lines, same order"),
        ],
        implementation=_impl("TrustSignals", ("Icon", "lucide")),
        animation_capabilities=["fade", "fade_up", "stagger", "none"],
        design_metadata=DesignMetadata(conversion_role="trust"),
        responsive_behavior=_grid(4),
    ),
    ComponentDefinition(
        id="reviews",
        category=C.commerce,
        description="Rating summary with distribution bars and verified review cards",
        capabilities=["trust", "reviews", "commerce", "social_proof"],
        variants=["standard", "compact"],
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="rating", description="average, e.g. 4.8"),
            S(name="count", description="number of reviews"),
            S(name="recommend"),
            S(name="cta"),
            S(name="more_cta"),
        ],
        implementation=_impl(
            "Reviews",
            ("Progress", "native", "distribution"),
            ("Avatar", "radix"),
            ("Card", "shadcn"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger"],
        design_metadata=DesignMetadata(conversion_role="trust"),
    ),
    ComponentDefinition(
        id="related_products",
        category=C.commerce,
        description="Cross-sell products as a carousel or a grid of product cards",
        capabilities=["commerce", "cross_sell"],
        supported_domains=_SHOP,
        variants=["carousel", "grid"],
        slots=_header_slots("cta"),
        allowed_children=["product_card"],
        implementation=_impl(
            "RelatedProducts", ("Carousel", "embla"), ("ProductCard", "native", "items")
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "slide"],
        design_metadata=DesignMetadata(conversion_role="cross_sell"),
        responsive_behavior=_grid(4),
    ),
    ComponentDefinition(
        id="product_filters",
        category=C.commerce,
        description=(
            "Listing controls: category navigation, search, filter chips, sort and result count. "
            "bar and chips lead a listing page with an h1; toolbar is a heading-less bar "
            "for use under a category_hero"
        ),
        capabilities=["commerce", "browse", "filter", "sort", "search"],
        supported_domains=_SHOP,
        variants=["bar", "chips", "toolbar"],
        default_variant="bar",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="subtitle"),
            S(name="count", description="number of results"),
            S(name="count_label"),
            S(name="categories", description=_LIST),
            S(name="filters", description=_LIST),
            S(name="sort_options", description=_LIST),
            S(name="sort_label"),
            S(name="filter_label"),
            S(name="search_placeholder"),
        ],
        implementation=_impl(
            "ProductFilters",
            ("Select", "native", "sort"),
            ("Input", "native", "search"),
            ("ToggleGroup", "native", "filters"),
        ),
        animation_capabilities=["fade", "none"],
        design_metadata=DesignMetadata(conversion_role="browse"),
    ),
    ComponentDefinition(
        id="cart_items",
        category=C.commerce,
        description=(
            "Cart line items with quantity, remove and save to wishlist; standard is a cart page "
            "lead (h1, free-delivery progress), compact is a condensed bag list"
        ),
        capabilities=["commerce", "cart", "purchase_preparation"],
        supported_domains=_SHOP,
        variants=["standard", "compact"],
        slots=[
            S(name="title"),
            S(name="free_shipping_threshold", description="e.g. $120"),
            S(name="free_shipping_note"),
            S(name="continue_cta"),
            S(name="note"),
        ],
        implementation=_impl(
            "CartItems",
            ("Image", "native"),
            ("QuantityStepper", "native", "quantity"),
            ("Button", "shadcn", "remove"),
        ),
        animation_capabilities=["fade", "stagger", "none"],
    ),
    ComponentDefinition(
        id="order_summary",
        category=C.commerce,
        description=(
            "Subtotal, delivery, discount, tax, total. standard adds discount code, gift note and "
            "a checkout action; compact lists items with no button (sits beside a checkout "
            "form)"
        ),
        capabilities=["commerce", "cart", "checkout", "conversion"],
        supported_domains=_SHOP,
        variants=["standard", "compact"],
        slots=[
            S(name="title"),
            S(name="subtotal"),
            S(name="shipping"),
            S(name="discount"),
            S(name="tax"),
            S(name="total"),
            S(name="subtotal_label"),
            S(name="shipping_label"),
            S(name="discount_label"),
            S(name="tax_label"),
            S(name="total_label"),
            S(name="currency"),
            S(name="primary_cta"),
            S(name="note"),
            S(name="delivery_title"),
            S(name="delivery_note"),
            S(name="gift_title"),
            S(name="gift_note"),
        ],
        implementation=_impl(
            "OrderSummary",
            ("Card", "shadcn"),
            ("Input", "native", "discount_code"),
            ("Button", "shadcn", "proceed"),
        ),
        animation_capabilities=["fade", "none"],
        design_metadata=DesignMetadata(conversion_role="primary_cta"),
    ),
    ComponentDefinition(
        id="collection_grid",
        category=C.commerce,
        description=(
            "Featured collections as large image tiles with title, count and a hover reveal; "
            "three_up grid, asymmetric (one tall + two), or carousel"
        ),
        capabilities=["commerce", "browse", "collections", "navigation"],
        supported_domains=_SHOP,
        supported_layouts=["grid", "asymmetric_grid"],
        variants=["three_up", "asymmetric", "carousel"],
        default_variant="three_up",
        slots=[
            *_header_slots("cta"),
            S(name="collections", description=_LIST),
            S(name="counts", description="comma-separated, e.g. 24 products"),
            S(name="descriptions", description="comma-separated one-liners, same order"),
            S(
                name="media",
                description="comma-separated subjects, same order: bag, leaf, glass...",
            ),
            S(name="tile_cta"),
        ],
        implementation=_impl(
            "CollectionGrid",
            ("Grid", "native"),
            ("Carousel", "embla"),
            ("Image", "native"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "reveal", "scale"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "editorial", "modern"], conversion_role="browse"
        ),
        responsive_behavior=_grid(3),
    ),
    ComponentDefinition(
        id="promo_banner",
        category=C.commerce,
        description=(
            "Seasonal or promotional campaign with headline, offer, code, countdown text and CTA; "
            "standard split band with media, strip announcement bar, or overlay on full-bleed media"
        ),
        capabilities=["promotion", "conversion", "campaign"],
        variants=["standard", "strip", "overlay"],
        slots=[
            S(name="eyebrow"),
            S(name="headline"),
            S(name="body"),
            S(name="offer", description="e.g. 20% off"),
            S(name="offer_note"),
            S(name="code", description="promo code"),
            S(name="countdown", description="e.g. Ends Sunday at midnight"),
            S(name="cta"),
            S(name="media", description=_MEDIA),
            S(name="media_label"),
        ],
        implementation=_impl("PromoBanner", ("Image", "native"), ("Button", "shadcn", "cta")),
        animation_capabilities=["fade", "fade_up", "reveal", "parallax", "none"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "bold", "modern"], conversion_role="primary_cta"
        ),
    ),
    ComponentDefinition(
        id="product_customizer",
        category=C.commerce,
        description=(
            "Standalone drink / product configurator: size, temperature, milk, sweetness, extras, "
            "quantity and a live price summary with add to cart. standard = media + options, "
            "stepped = numbered steps with sticky summary, compact = single card"
        ),
        capabilities=["commerce", "customization", "conversion", "configurator"],
        supported_domains=["ecommerce", "restaurant", "cafe", "food_beverage"],
        variants=["standard", "stepped", "compact"],
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="description"),
            S(name="product_name"),
            S(name="base_price", description="e.g. $4.50"),
            S(name="sizes", description=_OPTIONS),
            S(name="size_prices", description=_PRICES),
            S(name="temperatures", description=_OPTIONS),
            S(name="milks", description=_OPTIONS),
            S(name="milk_prices", description=_PRICES),
            S(name="sweetness", description=_OPTIONS),
            S(name="extras", description=_OPTIONS + " (multi-select)"),
            S(name="extra_prices", description=_PRICES),
            S(name="size_label"),
            S(name="temperature_label"),
            S(name="milk_label"),
            S(name="sweetness_label"),
            S(name="extras_label"),
            S(name="summary_label"),
            S(name="primary_cta"),
            S(name="media", description=_MEDIA),
        ],
        implementation=_impl(
            "ProductCustomizer",
            ("ToggleGroup", "radix", "options"),
            ("Stepper", "native", "quantity"),
            ("Card", "shadcn", "summary"),
            ("Button", "shadcn", "add_to_cart"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "number_ticker"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "modern", "playful"], conversion_role="primary_cta"
        ),
    ),
    ComponentDefinition(
        id="search_bar",
        category=C.commerce,
        description=(
            "Prominent product search with popular suggestions and recent-search chips; standard "
            "centred band, inline toolbar, or expanded with a suggestion and product preview panel"
        ),
        capabilities=["search", "browse", "discovery"],
        variants=["standard", "inline", "expanded"],
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="placeholder"),
            S(name="cta"),
            S(name="suggestions", description=_LIST),
            S(name="recent", description=_LIST),
            S(name="suggestions_label"),
            S(name="recent_label"),
            S(name="products_label"),
            S(name="all_results_cta"),
        ],
        implementation=_impl(
            "SearchBar", ("Input", "native", "search"), ("Button", "shadcn", "submit")
        ),
        animation_capabilities=["fade", "fade_up", "none"],
        design_metadata=DesignMetadata(conversion_role="browse"),
    ),
    ComponentDefinition(
        id="category_hero",
        category=C.commerce,
        description=(
            "Listing page header (h1): breadcrumb, category title, description, count, media and "
            "sub-category chips; standard split, banner over wide media, or minimal with image "
            "sub-category bubbles"
        ),
        capabilities=["commerce", "browse", "page_header", "navigation"],
        supported_domains=_SHOP,
        supported_layouts=["split", "full_bleed", "centered"],
        variants=["standard", "banner", "minimal"],
        slots=[
            S(name="title"),
            S(name="description"),
            S(name="count", description="e.g. 48 products"),
            S(name="breadcrumb", description="comma-separated parent pages"),
            S(name="subcategories", description=_LIST),
            S(name="media", description=_MEDIA),
            S(name="media_label"),
            S(name="media_note"),
        ],
        implementation=_impl(
            "CategoryHero", ("Breadcrumb", "native"), ("Image", "native"), ("ToggleGroup", "native")
        ),
        animation_capabilities=["fade", "fade_up", "reveal", "parallax"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "editorial", "minimal"], conversion_role="browse"
        ),
    ),
    ComponentDefinition(
        id="product_spotlight",
        category=C.commerce,
        description=(
            "One hero product told editorially: large media, story, key notes, price and CTA; "
            "standard split with detail image, centred with notes either side, or inverse band"
        ),
        capabilities=["commerce", "storytelling", "featured_product", "conversion"],
        supported_domains=_SHOP,
        supported_layouts=["split", "media_text", "centered"],
        variants=["standard", "centered", "inverse"],
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="story"),
            S(name="notes", description="comma-separated note labels"),
            S(name="note_details", description="comma-separated note values, same order"),
            S(name="price"),
            S(name="price_label"),
            S(name="badge"),
            S(name="primary_cta"),
            S(name="secondary_cta"),
            S(name="media", description=_MEDIA),
            S(name="media_label"),
        ],
        implementation=_impl(
            "ProductSpotlight",
            ("Image", "native"),
            ("Button", "shadcn", "cta"),
            ("motion.div", "motion"),
        ),
        animation_capabilities=["fade", "fade_up", "reveal", "parallax", "float", "scale"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "editorial", "bold"], conversion_role="primary_cta"
        ),
    ),
    ComponentDefinition(
        id="subscription_offer",
        category=C.commerce,
        description=(
            "Subscribe & save: one-time or subscription plan choice, delivery frequency, perks "
            "and CTA; standard centred plan cards or split with media"
        ),
        capabilities=["commerce", "subscription", "conversion", "retention"],
        supported_domains=_SHOP,
        variants=["standard", "split"],
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="body"),
            S(name="discount", description="e.g. Save 15%"),
            S(name="one_time_price"),
            S(name="subscribe_price"),
            S(name="one_time_label"),
            S(name="subscribe_label"),
            S(name="one_time_note"),
            S(name="subscribe_note"),
            S(name="frequencies", description=_LIST),
            S(name="frequency_label"),
            S(name="perks", description=_LIST),
            S(name="primary_cta"),
            S(name="secondary_cta"),
            S(name="fine_print"),
            S(name="media", description=_MEDIA),
            S(name="media_label"),
        ],
        implementation=_impl(
            "SubscriptionOffer",
            ("RadioGroup", "radix", "plan"),
            ("ToggleGroup", "radix", "frequency"),
            ("Button", "shadcn", "subscribe"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "none"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "modern"], conversion_role="primary_cta"
        ),
    ),
    ComponentDefinition(
        id="lookbook",
        category=C.commerce,
        description=(
            "Editorial image grid; hotspots variant has shoppable product pins over imagery, "
            "captions variant is a staggered gallery with a product link per look"
        ),
        capabilities=["commerce", "storytelling", "shoppable", "gallery"],
        supported_domains=_SHOP,
        supported_layouts=["asymmetric_grid", "grid"],
        variants=["hotspots", "captions"],
        default_variant="hotspots",
        slots=[
            *_header_slots("cta"),
            S(name="looks", description="comma-separated look titles"),
            S(name="captions", description="comma-separated look captions, same order"),
            S(name="products", description="comma-separated product names for the pins / links"),
            S(name="look_cta"),
        ],
        implementation=_impl(
            "Lookbook", ("Image", "native"), ("Button", "native", "hotspot"), ("Card", "shadcn")
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "reveal", "parallax"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "editorial"], conversion_role="browse"
        ),
        responsive_behavior=_grid(4),
    ),
    ComponentDefinition(
        id="menu_list",
        category=C.commerce,
        description=(
            "Cafe / restaurant menu: grouped items with names, descriptions, prices and dietary "
            "tags; standard two columns with leaders, tabs with item cards, or inverse board"
        ),
        capabilities=["menu", "commerce", "browse", "pricing"],
        supported_domains=["restaurant", "cafe", "food_beverage", "ecommerce"],
        variants=["standard", "tabs", "board"],
        slots=[
            *_header_slots(),
            S(name="groups", description="comma-separated menu section names"),
            S(name="note", description="allergen or milk note under the menu"),
        ],
        implementation=_impl("MenuList", ("Tabs", "radix", "tabs"), ("Badge", "shadcn", "tags")),
        animation_capabilities=["fade", "fade_up", "stagger", "none"],
        responsive_behavior=_grid(2),
    ),
]
