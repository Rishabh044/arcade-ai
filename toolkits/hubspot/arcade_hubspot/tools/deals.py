from typing import Annotated, Literal

from arcade.core.schema import ToolContext
from arcade.sdk import tool

from .utils import (
    fetch_associated_deal_ids,
    fetch_contact_id_by_email,
    fetch_hubspot_account_id,
    update_deal_priority,
)


@tool
async def set_deal_priority_for_contact(
    context: ToolContext,
    email: Annotated[str, "The email address of the contact"],
    priority: Annotated[Literal["high", "medium", "low"], "The priority to set on the deal"],
) -> Annotated[str, "The result of the operation"]:
    """Find the deals associated with a contact by email and flag them as high priority."""

    hubspot_token = context.get_secret("hubspot")

    account_id = await fetch_hubspot_account_id(hubspot_token)

    contact_id = await fetch_contact_id_by_email(hubspot_token, email)
    if not contact_id:
        return f"No contact found with email: {email}"

    deal_ids = await fetch_associated_deal_ids(hubspot_token, contact_id)
    if not deal_ids:
        return f"No deals associated with contact ID: {contact_id}"

    await update_deal_priority(hubspot_token, deal_ids[0], priority)
    return f"Set {priority} priority on https://app.hubspot.com/contacts/{account_id}/record/0-3/{deal_ids[0]}"
