"""Content components. Implementation mappings live here, never in agents."""

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

_MEDIA = "what the image shows: cup, bag, leaf, glass, product, person, space..."
_EDITORIAL = DesignMetadata(visual_styles=["editorial", "premium", "minimal"])
_STACK = ResponsiveBehavior(rules={"mobile": {"columns": 1}})


def _numbered(name: str, count: int, description: str) -> list[S]:
    return [S(name=f"{name}_{i}", description=description) for i in range(1, count + 1)]


COMPONENTS: list[ComponentDefinition] = [
    ComponentDefinition(
        id="faq",
        category=C.content,
        description=(
            "Accordion of frequently asked questions; two_column adds a heading, intro and "
            "contact nudge beside it"
        ),
        capabilities=["faq", "support", "objection_handling", "accordion"],
        supported_domains=_ALL,
        variants=["standard", "two_column"],
        default_variant="standard",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="intro"),
            *_numbered("question", 6, "one question; only filled pairs render"),
            *_numbered("answer", 6, "answer to the matching question"),
            S(name="contact_title"),
            S(name="contact_body"),
            S(name="contact_cta"),
            S(name="contact_name", description="person shown in the contact nudge"),
        ],
        implementation=_impl(
            "FAQ",
            ("Accordion", "radix", "questions"),
            ("Avatar", "native", "contact"),
            ("Button", "shadcn", "contact_cta"),
        ),
        animation_capabilities=["none", "fade", "fade_up"],
        responsive_behavior=_STACK,
        design_metadata=DesignMetadata(
            visual_styles=["editorial", "premium", "minimal"], conversion_role="support"
        ),
    ),
    ComponentDefinition(
        id="brand_story",
        category=C.content,
        description=(
            "Asymmetric image with long-form brand story, pull quote and founder signature"
        ),
        capabilities=["story", "about", "brand", "trust", "long_form", "media"],
        supported_domains=_ALL,
        supported_layouts=["split", "asymmetric", "stacked"],
        variants=["image_left", "overlap", "stacked"],
        default_variant="image_left",
        slots=[
            S(name="eyebrow"),
            S(name="title", required=True),
            S(name="body", description="opening paragraph (set as a lead with a drop cap)"),
            S(name="body_2", description="second paragraph"),
            S(name="quote", description="pull quote, without quotation marks"),
            S(name="signature", description="founder or author name"),
            S(name="signature_role"),
            S(name="cta"),
            S(name="media", description=_MEDIA),
            S(name="media_label"),
            S(name="detail_label", description="alt text for the small detail image"),
        ],
        implementation=_impl(
            "BrandStory",
            ("Media", "native", "image"),
            ("Blockquote", "native", "pull_quote"),
            ("Button", "shadcn", "cta"),
        ),
        animation_capabilities=["none", "fade", "fade_up", "reveal", "parallax"],
        responsive_behavior=_STACK,
        design_metadata=DesignMetadata(
            visual_styles=["editorial", "premium", "warm"], conversion_role="trust"
        ),
    ),
    ComponentDefinition(
        id="media_text",
        category=C.content,
        description="Alternating media and text feature rows with an optional stat per row",
        capabilities=["features", "story", "process", "media", "stats"],
        supported_domains=_ALL,
        supported_layouts=["media_text", "split", "alternating"],
        variants=["alternating", "reversed", "stats"],
        default_variant="alternating",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="intro"),
            S(name="items", description="comma-separated row titles (up to 4)"),
            *_numbered("body", 4, "body copy for the matching row"),
            S(name="stats", description="comma-separated stat values, one per row"),
            S(name="stat_labels", description="comma-separated stat labels, one per row"),
            S(name="link_label"),
        ],
        implementation=_impl(
            "MediaText", ("Media", "native", "image"), ("Button", "shadcn", "link")
        ),
        animation_capabilities=["none", "fade", "fade_up", "reveal", "stagger", "parallax"],
        responsive_behavior=_STACK,
        design_metadata=_EDITORIAL,
    ),
    ComponentDefinition(
        id="manifesto",
        category=C.content,
        description=(
            "Large typographic statement at display size with highlighted words and generous "
            "whitespace"
        ),
        capabilities=["statement", "brand", "values", "typography"],
        supported_domains=_ALL,
        variants=["standard", "inverse", "split"],
        default_variant="standard",
        slots=[
            S(name="eyebrow"),
            S(name="statement", required=True),
            S(
                name="highlight",
                description="comma-separated phrases from the statement to emphasise",
            ),
            S(name="signature"),
            S(name="signature_role"),
            S(name="body", description="short aside (split variant)"),
            S(name="cta", description="link (split variant)"),
        ],
        implementation=_impl("Manifesto", ("Typography", "native", "statement")),
        animation_capabilities=["none", "fade", "fade_up", "reveal", "stagger"],
        design_metadata=DesignMetadata(visual_styles=["editorial", "premium", "bold", "minimal"]),
    ),
    ComponentDefinition(
        id="editorial_quote",
        category=C.content,
        description="Single large pull quote with attribution; optional portrait or dark band",
        capabilities=["quote", "testimonial", "trust", "typography"],
        supported_domains=_ALL,
        variants=["centered", "with_media", "band"],
        default_variant="centered",
        slots=[
            S(name="quote", required=True, description="without quotation marks"),
            S(name="author"),
            S(name="role"),
            S(name="eyebrow", description="band variant"),
            S(name="media", description=_MEDIA),
            S(name="media_label"),
        ],
        implementation=_impl(
            "EditorialQuote", ("Blockquote", "native", "quote"), ("Avatar", "native", "author")
        ),
        animation_capabilities=["none", "fade", "fade_up", "reveal", "scale"],
        responsive_behavior=_STACK,
        design_metadata=DesignMetadata(
            visual_styles=["editorial", "premium", "minimal"], conversion_role="trust"
        ),
    ),
    ComponentDefinition(
        id="gallery_masonry",
        category=C.content,
        description="Masonry or mosaic image gallery with captions and varied aspect ratios",
        capabilities=["gallery", "media", "atmosphere", "portfolio"],
        supported_domains=_ALL,
        supported_layouts=["masonry", "mosaic", "grid"],
        variants=["masonry", "mosaic"],
        default_variant="masonry",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="intro"),
            S(name="captions", description="comma-separated image captions (6-7)"),
            S(name="cta"),
        ],
        implementation=_impl(
            "GalleryMasonry", ("Media", "native", "image"), ("Grid", "native", "mosaic")
        ),
        animation_capabilities=["none", "fade", "fade_up", "stagger", "scale", "reveal"],
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}, "desktop": {"columns": 3}}
        ),
        design_metadata=_EDITORIAL,
    ),
    ComponentDefinition(
        id="article_grid",
        category=C.content,
        description=(
            "Journal cards: a featured article with smaller ones, category tags and read time"
        ),
        capabilities=["blog", "journal", "articles", "content_hub", "browse"],
        supported_domains=_ALL,
        supported_layouts=["grid", "card_grid", "list"],
        variants=["featured", "grid", "list"],
        default_variant="featured",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="intro"),
            S(name="titles", description="comma-separated article titles (featured first)"),
            S(name="categories", description="comma-separated category tags"),
            S(name="read_times", description="comma-separated, e.g. 4 min read"),
            S(name="dates", description="comma-separated publish dates"),
            S(name="excerpt", description="excerpt for the featured article"),
            S(name="cta"),
        ],
        implementation=_impl(
            "ArticleGrid",
            ("Card", "native", "article"),
            ("Media", "native", "thumbnail"),
            ("Button", "shadcn", "cta"),
        ),
        animation_capabilities=_CARD_ANIMS,
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}, "desktop": {"columns": 3}}
        ),
        design_metadata=_EDITORIAL,
    ),
    ComponentDefinition(
        id="image_band",
        category=C.content,
        description="Full-bleed image band with a caption on a solid panel",
        capabilities=["media", "atmosphere", "story", "break"],
        supported_domains=_ALL,
        supported_layouts=["full_bleed"],
        variants=["caption_left", "caption_right", "letterbox"],
        default_variant="caption_left",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="caption"),
            S(name="cta"),
            S(name="media", description=_MEDIA),
            S(name="media_label"),
        ],
        implementation=_impl(
            "ImageBand", ("Media", "native", "image"), ("Button", "shadcn", "cta")
        ),
        animation_capabilities=["none", "fade", "reveal", "parallax", "scale"],
        design_metadata=DesignMetadata(visual_styles=["editorial", "premium", "immersive"]),
    ),
    ComponentDefinition(
        id="rich_text",
        category=C.content,
        description="Long-form prose with a comfortable measure, subheadings, list and blockquote",
        capabilities=["long_form", "prose", "policy", "about", "article"],
        supported_domains=_ALL,
        variants=["standard", "with_aside"],
        default_variant="standard",
        slots=[
            S(name="eyebrow"),
            S(name="title", required=True),
            S(name="meta", description="e.g. Updated September 2026"),
            S(name="lead"),
            S(name="heading_1"),
            S(name="body_1"),
            S(name="list", description="comma-separated list items"),
            S(name="heading_2"),
            S(name="body_2"),
            S(name="quote", description="without quotation marks"),
            S(name="quote_author"),
            S(name="body_3"),
        ],
        implementation=_impl("RichText", ("Prose", "native"), ("Nav", "native", "contents")),
        animation_capabilities=["none", "fade", "fade_up"],
        responsive_behavior=_STACK,
        design_metadata=_EDITORIAL,
    ),
    ComponentDefinition(
        id="contact_section",
        category=C.content,
        description="Contact details beside a labelled enquiry form",
        capabilities=["contact", "form", "lead_capture", "support"],
        supported_domains=_ALL,
        supported_layouts=["split", "stacked"],
        variants=["split", "stacked"],
        default_variant="split",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="intro"),
            S(name="email"),
            S(name="phone"),
            S(name="address"),
            S(name="hours"),
            S(name="form_title"),
            S(name="topics", description="comma-separated enquiry topics"),
            S(name="submit"),
            S(name="privacy"),
        ],
        implementation=_impl(
            "ContactSection",
            ("Input", "native", "fields"),
            ("Select", "native", "topic"),
            ("Textarea", "native", "message"),
            ("Button", "shadcn", "submit"),
        ),
        animation_capabilities=["none", "fade", "fade_up"],
        responsive_behavior=_STACK,
        design_metadata=DesignMetadata(
            visual_styles=["editorial", "premium", "minimal"], conversion_role="lead_capture"
        ),
    ),
    ComponentDefinition(
        id="location_hours",
        category=C.content,
        description="Store or cafe locations with address, opening hours table, map and directions",
        capabilities=["locations", "hours", "visit", "local", "map"],
        supported_domains=_ALL,
        supported_layouts=["split", "grid"],
        variants=["single", "multiple"],
        default_variant="single",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="intro"),
            S(name="locations", description="comma-separated location names"),
            *_numbered("address", 3, "address of the matching location"),
            S(name="days", description="comma-separated day ranges"),
            S(name="times", description="comma-separated opening times, one per day range"),
            S(name="note", description="holiday or access note"),
            S(name="phone"),
            S(name="directions_cta"),
        ],
        implementation=_impl(
            "LocationHours",
            ("Map", "native", "map"),
            ("Table", "native", "hours"),
            ("Button", "shadcn", "directions"),
        ),
        animation_capabilities=["none", "fade", "fade_up", "stagger"],
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}, "desktop": {"columns": 3}}
        ),
        design_metadata=DesignMetadata(
            visual_styles=["editorial", "premium", "warm"], conversion_role="visit"
        ),
    ),
    ComponentDefinition(
        id="newsletter_signup",
        category=C.marketing,
        description="Email capture with value proposition, perks and a privacy note",
        capabilities=["newsletter", "email_capture", "lead_capture", "conversion"],
        supported_domains=_ALL,
        variants=["inline", "card", "band"],
        default_variant="inline",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="body"),
            S(name="perks", description="comma-separated reasons to subscribe"),
            S(name="placeholder"),
            S(name="submit"),
            S(name="privacy"),
            S(name="media", description=_MEDIA + " (card variant)"),
            S(name="media_label"),
        ],
        implementation=_impl(
            "NewsletterSignup",
            ("Input", "native", "email"),
            ("Button", "shadcn", "submit"),
            ("Media", "native", "image"),
        ),
        animation_capabilities=["none", "fade", "fade_up", "glow"],
        responsive_behavior=_STACK,
        design_metadata=DesignMetadata(
            visual_styles=["editorial", "premium", "minimal"], conversion_role="lead_capture"
        ),
    ),
    ComponentDefinition(
        id="feature_split",
        category=C.content,
        description=("Large media (sticky on desktop) beside a list of 3-4 benefits with icons"),
        capabilities=["features", "benefits", "media", "value_proposition"],
        supported_domains=_ALL,
        supported_layouts=["split", "media_text"],
        variants=["media_left", "media_right", "grid"],
        default_variant="media_left",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="intro"),
            S(name="items", description="comma-separated benefit titles (3-4)"),
            *_numbered("body", 4, "body copy for the matching benefit"),
            S(
                name="icons",
                description=(
                    "comma-separated: leaf, sparkles, recycle, heart, truck, shield, gift, "
                    "clock, award, hand"
                ),
            ),
            S(name="media", description=_MEDIA),
            S(name="media_label"),
            S(name="badge", description="short caption on the image"),
            S(name="cta"),
        ],
        implementation=_impl(
            "FeatureSplit",
            ("Media", "native", "image"),
            ("Icon", "lucide", "benefit"),
            ("Button", "shadcn", "cta"),
        ),
        animation_capabilities=["none", "fade", "fade_up", "stagger", "reveal"],
        responsive_behavior=_STACK,
        design_metadata=_EDITORIAL,
    ),
]
