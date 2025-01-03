import os

import httpx

# Replace with your HubSpot API token
api_token = os.getenv("HUBSPOT_API_TOKEN")
headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}


async def fetch_hubspot_account_id() -> str:
    account_info_url = "https://api.hubapi.com/account-info/v3/details"
    async with httpx.AsyncClient() as client:
        response = await client.get(account_info_url, headers=headers)
        response.raise_for_status()
        account_info = response.json()
        return account_info.get("portalId")


async def fetch_contact_id_by_email(email):
    contact_search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    search_payload = {
        "filterGroups": [
            {"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}
        ],
        "properties": ["email"],
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(contact_search_url, headers=headers, json=search_payload)
        response.raise_for_status()
        contact_data = response.json()
        return contact_data["results"][0]["id"] if contact_data["results"] else None


async def fetch_associated_deal_ids(contact_id) -> list[str]:
    associations_url = (
        f"https://api.hubapi.com/crm/v4/objects/contacts/{contact_id}/associations/deals"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(associations_url, headers=headers)
        response.raise_for_status()
        associations_data = response.json()
        return (
            [assoc["toObjectId"] for assoc in associations_data["results"]]
            if associations_data["results"]
            else []
        )


async def update_deal_priority(deal_id: str, priority: str) -> dict:
    update_deal_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
    update_payload = {"properties": {"hs_priority": priority}}
    async with httpx.AsyncClient() as client:
        # Update the deal priority
        patch_response = await client.patch(update_deal_url, headers=headers, json=update_payload)
        patch_response.raise_for_status()
        return patch_response.json()
