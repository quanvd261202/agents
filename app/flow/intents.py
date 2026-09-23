"""The intent vocabulary. A planner edge says what the visitor means to do (`open_item`,
`checkout`), never which control does it; components declare which intents they emit, and the
resolver joins the two into hrefs."""

from __future__ import annotations

from pydantic import Field

from app.core.exceptions import ValidationError
from app.core.registry import BaseRegistry
from app.models.common import StrictModel


class UnknownIntentError(ValidationError): ...


class IntentDefinition(StrictModel):
    id: str
    description: str
    #: Page types the target screen may be built from. Empty means any page.
    page_types: list[str] = Field(default_factory=list)
    #: The target is opened for one item of a collection, so its route carries an `:id` segment.
    per_item: bool = False
    #: The target is the screen at `/`.
    home: bool = False


INTENTS: list[IntentDefinition] = [
    IntentDefinition(id="go_home", description="return to the entry screen", home=True),
    IntentDefinition(
        id="browse",
        description="see everything on offer: the catalogue, the listing",
        page_types=["product_listing", "storefront"],
    ),
    IntentDefinition(
        id="open_item",
        description="open one listed thing (a product, course, plan, article) on its own page",
        page_types=["product_detail"],
        per_item=True,
    ),
    IntentDefinition(
        id="add_to_cart", description="put the item in the cart and go there", page_types=["cart"]
    ),
    IntentDefinition(id="view_cart", description="see what is in the cart", page_types=["cart"]),
    IntentDefinition(id="checkout", description="pay for the cart", page_types=["checkout"]),
    IntentDefinition(id="sign_in", description="log in to an existing account"),
    IntentDefinition(id="sign_up", description="create an account, start a trial, enrol"),
    IntentDefinition(id="learn_more", description="read more about the offer or the brand"),
    IntentDefinition(id="compare_plans", description="see prices and plans"),
    IntentDefinition(id="contact", description="get in touch, book a demo, ask a question"),
    IntentDefinition(
        id="open_dashboard", description="go to the signed-in workspace", page_types=["dashboard"]
    ),
    IntentDefinition(
        id="open_settings",
        description="change account or workspace settings",
        page_types=["settings"],
    ),
]


class IntentRegistry(BaseRegistry[IntentDefinition]):
    kind = "intent"
    not_found_error = UnknownIntentError

    def describe(self) -> str:
        return "\n".join(f"- {i.id}: {i.description}" for i in self)


def default_intent_registry() -> IntentRegistry:
    return IntentRegistry(INTENTS)
