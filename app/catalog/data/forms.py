"""Forms components. Implementation mappings live here, never in agents."""

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

_APP = ["saas", "dashboard", "admin"]

COMPONENTS: list[ComponentDefinition] = [
    ComponentDefinition(
        id="checkout_form",
        category=C.forms,
        description=(
            "Single-page checkout: contact, shipping address, delivery method choice and card "
            "payment, with labelled fields and progress indication. standard is a numbered "
            "four-step form with a stepper; express leads with one-tap wallet buttons, then a "
            "condensed two-step form with a progress bar."
        ),
        capabilities=["commerce", "checkout", "forms", "purchase", "payment", "shipping"],
        supported_domains=["ecommerce"],
        variants=["standard", "express"],
        slots=[
            S(name="title", description="page heading, e.g. Checkout"),
            S(name="subtitle", description="line under the heading (express)"),
            S(name="eyebrow", description="label above the heading (standard)"),
            S(name="total", description="order total shown on the pay button"),
            S(name="cta", description="pay button label"),
            S(name="secure_note", description="reassurance under the pay button"),
            S(name="express_title", description="caption above wallet buttons (express)"),
            S(name="express_methods", description="comma list of wallet names (express)"),
        ],
        implementation=_impl(
            "CheckoutForm",
            ("Input", "shadcn"),
            ("Select", "native"),
            ("RadioGroup", "native", "delivery method"),
            ("Stepper", "native", "progress"),
            ("Button", "shadcn", "express_pay"),
            ("Button", "shadcn", "place_order"),
        ),
        animation_capabilities=["fade", "fade_up", "none"],
        design_metadata=DesignMetadata(conversion_role="primary_cta"),
    ),
    ComponentDefinition(
        id="auth_form",
        emits={"cta": ["open_dashboard", "go_home"]},
        category=C.forms,
        description=(
            "Sign in / sign up form with social buttons, labelled email and password fields, "
            "show-password toggle and forgot-password link. signin is a centred card; signup adds "
            "name, live password requirements and terms; split places the sign-in form beside a "
            "full-height brand image with a testimonial."
        ),
        capabilities=["auth", "sign_in", "sign_up", "login", "forms", "onboarding"],
        supported_domains=_ALL,
        variants=["signin", "signup", "split"],
        default_variant="signin",
        slots=[
            S(name="title", description="heading, e.g. Welcome back"),
            S(name="subtitle", description="one line under the heading"),
            S(name="cta", description="submit button label"),
            S(name="brand", description="brand name beside the logo mark"),
            S(name="social", description="comma list of sign-in providers"),
            S(name="forgot_link", description="forgot-password link text"),
            S(name="footer_prompt", description="e.g. New here?"),
            S(name="footer_link", description="e.g. Create an account"),
            S(name="legal", description="lead-in to the Terms / Privacy links"),
            S(name="media", description="split variant: " + _MEDIA),
            S(name="media_label", description="image description (split)"),
            S(name="quote", description="testimonial over the image (split)"),
            S(name="quote_author", description="testimonial author (split)"),
            S(name="quote_role", description="author role (split)"),
        ],
        implementation=_impl(
            "AuthForm",
            ("Card", "shadcn"),
            ("Input", "shadcn"),
            ("Checkbox", "native"),
            ("Button", "shadcn", "submit"),
            ("Button", "shadcn", "social"),
            ("Image", "native", "brand media"),
        ),
        animation_capabilities=["fade", "fade_up", "scale", "none"],
        design_metadata=DesignMetadata(conversion_role="primary_cta"),
    ),
    ComponentDefinition(
        id="settings_navigation",
        category=C.forms,
        description=(
            "Secondary nav between settings sections. tabs is an underline tab bar that scrolls "
            "on phones; vertical is a grouped rail with icons that becomes tabs on phones."
        ),
        capabilities=["navigation", "settings", "tabs"],
        supported_domains=_APP,
        variants=["tabs", "vertical"],
        default_variant="tabs",
        slots=[
            S(name="title", description="accessible name of the nav"),
            S(name="items", description="comma list of settings sections"),
            S(name="groups", description="comma list of two group headings (vertical)"),
        ],
        implementation=_impl("SettingsNav", ("Tabs", "shadcn"), ("NavLink", "native")),
        animation_capabilities=["fade", "none"],
    ),
    ComponentDefinition(
        id="settings_form",
        category=C.forms,
        description=(
            "Grouped settings form section with save action. standard is a described section "
            "beside a profile form card (avatar, names, email, bio, selects); card is a single "
            "card of switch rows; inline is a list of rows each edited in place."
        ),
        capabilities=["settings", "form", "profile", "preferences", "notifications"],
        supported_domains=_APP,
        variants=["standard", "card", "inline"],
        slots=[
            S(name="title", required=True),
            S(name="description"),
            S(name="cta", description="save button label"),
            S(name="secondary_cta", description="cancel button label"),
        ],
        implementation=_impl(
            "SettingsForm",
            ("Form", "shadcn"),
            ("Input", "shadcn"),
            ("Switch", "radix"),
            ("Select", "native"),
            ("Avatar", "shadcn"),
            ("Button", "shadcn", "save"),
        ),
        animation_capabilities=["fade", "fade_up", "none"],
    ),
    ComponentDefinition(
        id="danger_zone",
        category=C.forms,
        description=(
            "Destructive actions isolated in a danger-bordered card: transfer, archive and a "
            "delete action guarded by a type-to-confirm dialog."
        ),
        capabilities=["settings", "destructive", "confirmation"],
        supported_domains=_APP,
        variants=["standard"],
        slots=[
            S(name="title"),
            S(name="description"),
            S(name="cta", description="destructive action label, e.g. Delete workspace"),
            S(name="body", description="what the destructive action removes"),
            S(name="confirm_word", description="word the user types to confirm"),
        ],
        implementation=_impl(
            "DangerZone",
            ("Card", "shadcn"),
            ("Dialog", "radix", "confirmation"),
            ("Button", "shadcn", "destructive"),
        ),
        animation_capabilities=["fade", "none"],
    ),
]
