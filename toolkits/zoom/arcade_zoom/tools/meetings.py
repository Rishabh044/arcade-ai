from typing import Annotated, Optional

from arcade.sdk import ToolContext, tool
from arcade.sdk.auth import Zoom

from ..utils import HttpMethod, double_encode_uuid, send_zoom_request


@tool(
    requires_auth=Zoom(
        scopes=["meeting:read:list_upcoming_meetings"],
    )
)
async def list_upcoming_meetings(
    context: ToolContext,
    user_id: Annotated[
        Optional[str],
        "The user's user ID or email address. Defaults to 'me' for the current user.",
    ] = "me",
) -> Annotated[dict, "List of upcoming meetings within the next 24 hours"]:
    """List a Zoom user's upcoming meetings within the next 24 hours."""
    endpoint = f"/users/{user_id}/upcoming_meetings"

    response = await send_zoom_request(context, HttpMethod.GET, endpoint)
    return response.json()


@tool(
    requires_auth=Zoom(
        scopes=["meeting:read:invitation"],
    )
)
async def get_meeting_invitation(
    context: ToolContext,
    meeting_id: Annotated[
        int,
        "The Zoom meeting ID",
    ],
) -> Annotated[dict, "Meeting invitation string"]:
    """Retrieve the invitation note for the provided Zoom meeting."""
    endpoint = f"/meetings/{meeting_id}/invitation"

    response = await send_zoom_request(context, HttpMethod.GET, endpoint)
    return response.json()


# NOTE: Parameters related to attendees are only available for paid accounts. The creator of this tool is not a paid user so they are untested
@tool(
    requires_auth=Zoom(
        scopes=["meeting:write:meeting"],
    )
)
async def create_instant_meeting(
    context: ToolContext,
    title: Annotated[str, "The title of the meeting"],
    description: Annotated[Optional[str], "The description of the meeting"] = None,
    password: Annotated[Optional[str], "The password required to join the meeting"] = None,
    alternative_host_emails: Annotated[
        Optional[list[str]], "The email addresses of the alternative hosts"
    ] = None,
    authentication_domains: Annotated[
        Optional[list[str]],
        "Authenticated domains. Only users with emails in these domains can join",
    ] = None,
    meeting_authentication: Annotated[
        Optional[bool], "If true, only authenticated users can join the meeting"
    ] = False,
    attendee_email_addresses: Annotated[
        Optional[list[str]], "The email addresses of the attendees"
    ] = None,
    waiting_room: Annotated[
        Optional[bool],
        "If true, participants will be placed in a waiting room before being admitted to the meeting",
    ] = False,
) -> Annotated[dict, "The created meeting"]:
    """Create an instant Zoom meeting that starts immediately"""
    endpoint = "/users/me/meetings"

    body = {
        "topic": title,
        "agenda": description,
        "password": password,
        "waiting_room": waiting_room,  # Whether to use the waiting room feature
        "meeting_authentication": meeting_authentication,
        "host_video": "false",  # Whether to start meetings with the host video on
        "mute_upon_entry": "true",
        "participant_video": "false",  # Whether to start the meeting with participants video on
        "registrants_confirmation_email": "true",  # Whether to send a confirmation email to registrants
        "registrants_email_notification": "true",  # Whether to send an email notification to the registrants
        "type": 1,
    }
    if alternative_host_emails:
        body["alternative_host_ids"] = ";".join(alternative_host_emails)
    if authentication_domains:
        body["authentication_domains"] = ",".join(authentication_domains)
    if attendee_email_addresses:
        body["meeting_invitees"] = [{"email": email} for email in attendee_email_addresses]

    response = await send_zoom_request(context, HttpMethod.POST, endpoint, json_data=body)

    return response.json()


# NOTE: Only available for Paid accounts
@tool(
    requires_auth=Zoom(
        scopes=["meeting:read:summary"],
    )
)
async def get_meeting_summary(
    context: ToolContext,
    meeting_uuid: Annotated[str, "The Zoom meeting UUID"],
) -> Annotated[dict, "The meeting summary"]:
    """Get the summary of a Zoom meeting given the meeting's UUID"""
    meeting_uuid = double_encode_uuid(meeting_uuid)

    endpoint = f"/meetings/{meeting_uuid}/meeting_summary"

    response = await send_zoom_request(context, HttpMethod.GET, endpoint)
    return response.json()
