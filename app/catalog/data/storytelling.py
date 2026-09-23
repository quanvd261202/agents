"""Storytelling components: proof, process and narrative sections that span marketing and content.
Implementation mappings live here, never in agents."""

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

_HEADER = [S(name="eyebrow"), S(name="title"), S(name="subtitle")]

COMPONENTS: list[ComponentDefinition] = [
    ComponentDefinition(
        id="testimonial_spotlight",
        category=C.marketing,
        description="One large testimonial: big quote, portrait, name, role, rating and company",
        capabilities=["trust", "testimonial", "quote", "social_proof", "responsive"],
        supported_domains=_ALL,
        supported_layouts=["split", "centered"],
        variants=["split", "centered", "editorial"],
        default_variant="split",
        slots=[
            S(name="eyebrow"),
            S(name="quote", required=True, description="the testimonial, one or two sentences"),
            S(name="name"),
            S(name="role"),
            S(name="company", description="company or publication shown as a wordmark"),
            S(name="rating", description="number from 1 to 5"),
            S(name="rating_note", description="line under the rating badge (split variant)"),
            S(name="media", description="what the portrait shows: person, space, product..."),
            S(name="media_label"),
        ],
        implementation=_impl(
            "TestimonialSpotlight",
            ("Media", "native", "portrait"),
            ("Rating", "native"),
            ("Quote", "lucide", "quote mark"),
        ),
        animation_capabilities=["fade", "fade_up", "reveal", "parallax"],
        design_metadata=DesignMetadata(
            visual_styles=["premium", "editorial", "minimal"], conversion_role="trust"
        ),
    ),
    ComponentDefinition(
        id="press_quotes",
        category=C.marketing,
        description="As-seen-in band of short press quotes with publication names",
        capabilities=["trust", "press", "social_proof", "logos"],
        supported_domains=_ALL,
        variants=["grid", "marquee"],
        default_variant="grid",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="quotes", description="comma-separated short quotes (no commas inside)"),
            S(name="publications", description="comma-separated publication names"),
            S(name="dates", description="comma-separated issue or date lines (grid variant)"),
        ],
        implementation=_impl("PressQuotes", ("Marquee", "native", "marquee variant")),
        animation_capabilities=["fade", "stagger", "marquee", "none"],
        design_metadata=DesignMetadata(
            visual_styles=["editorial", "premium", "minimal"], conversion_role="trust"
        ),
    ),
    ComponentDefinition(
        id="team_grid",
        category=C.content,
        description="Team members with portrait, name, role, short bio and social links",
        capabilities=["team", "about", "people", "trust", "grid", "responsive"],
        supported_domains=_ALL,
        supported_layouts=["grid", "card_grid"],
        variants=["grid", "compact"],
        default_variant="grid",
        slots=[
            *_HEADER,
            S(name="names", description="comma-separated names"),
            S(name="roles", description="comma-separated roles, parallel to names"),
            S(name="bios", description="comma-separated one-line bios (no commas inside)"),
            S(name="cta", description="link label, e.g. hiring"),
        ],
        implementation=_impl(
            "TeamGrid",
            ("Media", "native", "portrait"),
            ("Mail", "lucide", "social link"),
            ("Globe", "lucide", "social link"),
        ),
        animation_capabilities=_CARD_ANIMS,
        responsive_behavior=ResponsiveBehavior(
            rules={"mobile": {"columns": 1}, "tablet": {"columns": 2}, "desktop": {"columns": 4}}
        ),
        design_metadata=DesignMetadata(
            visual_styles=["editorial", "minimal", "warm"], conversion_role="trust"
        ),
    ),
    ComponentDefinition(
        id="timeline",
        category=C.content,
        description="Story milestones: vertical on mobile, alternating or horizontal on desktop",
        capabilities=["timeline", "story", "about", "history", "milestones"],
        supported_domains=_ALL,
        variants=["alternating", "horizontal"],
        default_variant="alternating",
        slots=[
            *_HEADER,
            S(name="years", description="comma-separated years or dates"),
            S(name="milestones", description="comma-separated milestone titles"),
            S(name="details", description="comma-separated one-line details (no commas inside)"),
        ],
        implementation=_impl("MilestoneTimeline", ("ol", "native", "timeline list")),
        animation_capabilities=["fade", "fade_up", "stagger", "reveal", "slide"],
        design_metadata=DesignMetadata(visual_styles=["editorial", "minimal", "premium"]),
    ),
    ComponentDefinition(
        id="steps",
        category=C.marketing,
        description="How it works: three or four numbered steps with icons and a connecting line",
        capabilities=["process", "how_it_works", "onboarding", "steps", "conversion"],
        supported_domains=_ALL,
        variants=["numbered", "cards"],
        default_variant="numbered",
        slots=[
            *_HEADER,
            S(name="steps", description="comma-separated step titles, three or four"),
            S(name="details", description="comma-separated one-line details (no commas inside)"),
            S(name="cta"),
        ],
        implementation=_impl(
            "HowItWorksSteps",
            ("Compass", "lucide", "step icon"),
            ("ArrowRight", "lucide", "connector"),
            ("Button", "native", "cta"),
        ),
        animation_capabilities=["fade", "fade_up", "stagger", "reveal"],
        design_metadata=DesignMetadata(
            visual_styles=["minimal", "modern", "premium"], conversion_role="education"
        ),
    ),
    ComponentDefinition(
        id="video_showcase",
        category=C.marketing,
        description="Large video poster with a labelled play button, caption and chapter list",
        capabilities=["video", "media", "showcase", "story"],
        supported_domains=_ALL,
        variants=["standard", "cinematic"],
        default_variant="standard",
        slots=[
            S(name="eyebrow"),
            S(name="title"),
            S(name="caption"),
            S(name="chapters", description="comma-separated chapter titles"),
            S(name="timestamps", description="comma-separated chapter start times, e.g. 1:24"),
            S(name="duration", description="e.g. 6 min film"),
            S(name="play_label"),
            S(name="media", description="what the poster shows: space, person, product..."),
            S(name="media_label"),
        ],
        implementation=_impl(
            "VideoShowcase",
            ("Media", "native", "poster"),
            ("Play", "lucide", "play button"),
            ("Clock", "lucide"),
        ),
        animation_capabilities=["fade", "fade_up", "scale", "reveal", "parallax"],
        design_metadata=DesignMetadata(
            visual_styles=["cinematic", "premium", "editorial"], conversion_role="engagement"
        ),
    ),
    ComponentDefinition(
        id="tabs_showcase",
        category=C.marketing,
        description="Feature tour: tabs that each swap a headline, copy, points and media",
        capabilities=["features", "tour", "tabs", "showcase", "interactive"],
        supported_domains=_ALL,
        variants=["split", "stacked"],
        default_variant="split",
        slots=[
            *_HEADER,
            S(name="tabs", description="comma-separated tab labels, up to four"),
            S(name="tabs_label", description="accessible name for the tab list"),
            S(name="headlines", description="comma-separated headline per tab"),
            S(name="bodies", description="comma-separated body per tab (no commas inside)"),
            S(name="points", description="comma-separated short proof points shown on every tab"),
            S(name="cta"),
        ],
        implementation=_impl(
            "TabsShowcase",
            ("Tabs", "radix"),
            ("Media", "native"),
            ("Check", "lucide", "points"),
        ),
        animation_capabilities=["fade", "fade_up", "slide", "morph"],
        design_metadata=DesignMetadata(
            visual_styles=["modern", "premium", "minimal"], conversion_role="education"
        ),
    ),
    ComponentDefinition(
        id="stats_band",
        category=C.marketing,
        description="Big-number band with labels and a footnote, usually in an inverse tone",
        capabilities=["stats", "trust", "numbers", "proof"],
        supported_domains=_ALL,
        variants=["band", "split"],
        default_variant="band",
        slots=[
            *_HEADER[:2],
            S(name="body", description="supporting paragraph (split variant)"),
            S(name="values", description="comma-separated short figures, e.g. 240k,98%"),
            S(name="labels", description="comma-separated labels, parallel to values"),
            S(name="footnote", description="source for the starred figure"),
        ],
        implementation=_impl("StatsBand", ("dl", "native", "figures")),
        animation_capabilities=["fade", "fade_up", "stagger", "number_ticker"],
        design_metadata=DesignMetadata(
            visual_styles=["bold", "editorial", "premium"], conversion_role="trust"
        ),
    ),
    ComponentDefinition(
        id="comparison_table",
        category=C.content,
        description="Us-vs-them or plan comparison table with check and cross marks",
        capabilities=["comparison", "pricing", "table", "conversion", "responsive"],
        supported_domains=_ALL,
        variants=["versus", "plans"],
        default_variant="versus",
        slots=[
            *_HEADER,
            S(name="rows", description="comma-separated features being compared"),
            S(name="columns", description="names; versus features the 1st, plans the 2nd"),
            S(name="cells", description="comma-separated values row by row: yes, no or short text"),
            S(name="feature_label", description="header over the feature column"),
            S(name="badge", description="badge on the highlighted column"),
            S(name="cta"),
            S(name="note", description="source line beside the cta (versus variant)"),
        ],
        implementation=_impl(
            "ComparisonTable",
            ("table", "native"),
            ("Check", "lucide", "included"),
            ("X", "lucide", "not included"),
            ("Badge", "native"),
        ),
        animation_capabilities=["fade", "fade_up", "none"],
        design_metadata=DesignMetadata(
            visual_styles=["minimal", "modern", "clean"], conversion_role="primary_cta"
        ),
    ),
]
