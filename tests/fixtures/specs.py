"""Golden DesignSpec fixtures: one per recipe, hand-written the way the LLM should write them."""

SAAS_LANDING = {
    "screen_id": "home",
    "recipe": "saas_landing",
    "visual_style": "premium_modern",
    "theme": "saas",
    "density": "comfortable",
    "sections": [
        {"id": "navigation", "type": "navigation", "variant": "transparent"},
        {
            "id": "hero",
            "type": "hero",
            "variant": "aurora",
            "content": {"headline": "Ship dashboards in minutes", "primary_cta": "Start free"},
        },
        {
            "id": "social_proof",
            "type": "social_proof",
            "variant": "marquee",
            "animation": {"name": "marquee"},
        },
        {
            "id": "features",
            "type": "feature_bento",
            "variant": "premium",
            "children": [
                {"id": f"f{i}", "type": "feature_card", "content": {"title": f"Feature {i}"}}
                for i in range(1, 5)
            ],
        },
        {
            "id": "metrics",
            "type": "metrics",
            "variant": "cards",
            "animation": {"name": "number_ticker", "intensity": "moderate"},
        },
        {"id": "testimonials", "type": "testimonial_grid"},
        {"id": "pricing", "type": "pricing_table", "variant": "highlighted"},
        {"id": "faq", "type": "faq"},
        {"id": "cta", "type": "cta", "variant": "gradient", "content": {"headline": "Ready?"}},
        {"id": "footer", "type": "footer"},
    ],
    "animation": {"name": "subtle_stagger", "intensity": "subtle"},
}

ECOMMERCE_PRODUCT = {
    "screen_id": "product_detail",
    "recipe": "ecommerce_product",
    "visual_style": "premium_modern",
    "theme": "premium_light",
    "density": "comfortable",
    "sections": [
        {"id": "navigation", "type": "navigation"},
        {"id": "breadcrumb", "type": "breadcrumb"},
        {
            "id": "product_detail",
            "type": "product_detail",
            "variant": "premium_split",
            "layout": {"type": "split", "ratio": "60/40", "gap": "xl"},
        },
        {"id": "trust_signals", "type": "trust_signals"},
        {"id": "reviews", "type": "reviews"},
        {
            "id": "related_products",
            "type": "related_products",
            "variant": "grid",
            "children": [
                {
                    "id": f"p{i}",
                    "type": "product_card",
                    "variant": "premium",
                    "content": {"image": "x", "title": f"Shoe {i}", "price": "$120"},
                }
                for i in range(1, 5)
            ],
        },
        {"id": "footer", "type": "footer", "variant": "minimal"},
    ],
    "animation": {"name": "subtle_stagger"},
}

DASHBOARD = {
    "screen_id": "overview",
    "recipe": "dashboard",
    "visual_style": "modern",
    "theme": "modern_dark",
    "density": "compact",
    "sections": [
        {"id": "sidebar", "type": "dashboard_sidebar", "variant": "compact"},
        {"id": "page_header", "type": "page_header", "content": {"title": "Overview"}},
        {
            "id": "stats",
            "type": "stats",
            "variant": "with_trend",
            "layout": {"type": "grid", "columns": 4},
        },
        {"id": "primary_visualization", "type": "chart_panel", "variant": "area"},
        {"id": "activity", "type": "activity_feed"},
        {"id": "secondary_content", "type": "data_table", "variant": "with_toolbar"},
    ],
}

SETTINGS = {
    "screen_id": "settings",
    "recipe": "settings",
    "visual_style": "minimal",
    "theme": "minimal",
    "sections": [
        {"id": "sidebar", "type": "dashboard_sidebar"},
        {"id": "page_header", "type": "page_header", "content": {"title": "Settings"}},
        {"id": "settings_navigation", "type": "settings_navigation", "variant": "vertical"},
        {
            "id": "settings_sections",
            "type": "settings_form",
            "variant": "card",
            "content": {"title": "Profile"},
        },
        {"id": "danger_zone", "type": "danger_zone"},
    ],
    "animation": {"name": "none"},
}

ECOMMERCE_HOME = {
    "screen_id": "home",
    "recipe": "ecommerce_home",
    "visual_style": "premium_modern",
    "theme": "premium_light",
    "density": "comfortable",
    "sections": [
        {"id": "navigation", "type": "navigation"},
        {"id": "hero", "type": "hero", "variant": "split"},
        {"id": "featured_products", "type": "product_grid", "variant": "premium"},
        {"id": "testimonials", "type": "reviews", "animation": {"name": "stagger"}},
        {"id": "brand_story", "type": "feature_bento"},
        {"id": "trust_signals", "type": "trust_signals", "variant": "inline"},
        {"id": "footer", "type": "footer"},
    ],
    "animation": {"name": "subtle", "intensity": "subtle"},
}

ECOMMERCE_LISTING = {
    "screen_id": "listing",
    "recipe": "ecommerce_listing",
    "visual_style": "premium_modern",
    "theme": "premium_light",
    "density": "comfortable",
    "sections": [
        {"id": "navigation", "type": "navigation"},
        {"id": "breadcrumb", "type": "breadcrumb"},
        {"id": "filters", "type": "product_filters", "variant": "chips"},
        {"id": "product_grid", "type": "product_grid", "animation": {"name": "stagger"}},
        {"id": "footer", "type": "footer"},
    ],
    "animation": {"name": "subtle", "intensity": "subtle"},
}

ECOMMERCE_CART = {
    "screen_id": "cart",
    "recipe": "ecommerce_cart",
    "visual_style": "premium_modern",
    "theme": "premium_light",
    "density": "comfortable",
    "sections": [
        {"id": "navigation", "type": "navigation"},
        {"id": "cart_items", "type": "cart_items"},
        {"id": "order_summary", "type": "order_summary"},
        {"id": "trust_signals", "type": "trust_signals"},
        {"id": "cross_sell", "type": "related_products", "variant": "grid"},
        {"id": "footer", "type": "footer"},
    ],
    "animation": {"name": "subtle", "intensity": "subtle"},
}

ECOMMERCE_CHECKOUT = {
    "screen_id": "checkout",
    "recipe": "ecommerce_checkout",
    "visual_style": "premium_modern",
    "theme": "premium_light",
    "density": "comfortable",
    "sections": [
        {"id": "navigation", "type": "navigation"},
        {"id": "checkout_form", "type": "checkout_form", "variant": "express"},
        {"id": "order_summary", "type": "order_summary", "variant": "compact"},
        {"id": "trust_signals", "type": "trust_signals", "variant": "inline"},
        {"id": "footer", "type": "footer"},
    ],
    "animation": {"name": "none"},
}

ALL = {
    "saas_landing": SAAS_LANDING,
    "ecommerce_home": ECOMMERCE_HOME,
    "ecommerce_listing": ECOMMERCE_LISTING,
    "ecommerce_product": ECOMMERCE_PRODUCT,
    "ecommerce_cart": ECOMMERCE_CART,
    "ecommerce_checkout": ECOMMERCE_CHECKOUT,
    "dashboard": DASHBOARD,
    "settings": SETTINGS,
}
