import arcade_zoom
from arcade_zoom.tools.meetings import (
    create_instant_meeting,
    get_meeting_invitation,
    get_meeting_summary,
    list_upcoming_meetings,
)

from arcade.sdk import ToolCatalog
from arcade.sdk.eval import (
    BinaryCritic,
    EvalRubric,
    EvalSuite,
    SimilarityCritic,
    tool_eval,
)

# Evaluation rubric
rubric = EvalRubric(
    fail_threshold=0.8,
    warn_threshold=0.9,
)


catalog = ToolCatalog()
catalog.add_module(arcade_zoom)

# This history is a conversation where the user asks for the upcoming Zoom meetings, and the assistant lists them.
list_upcoming_meetings_history = [
    {"role": "user", "content": "list my upcoming meetings"},
    {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": "call_fqZHT1DNcil1pbIv6UbOWVq9",
                "type": "function",
                "function": {"name": "Zoom_ListUpcomingMeetings", "arguments": "{}"},
            }
        ],
    },
    {
        "role": "tool",
        "content": '{"meeting_ids": [385572793583611134, 4388337744, 303948585686], "meeting_uuids": ["rfk42tj34ewrDFk43f//234g3wgh==", "2343f2tj34ewrDF34g3wzq==", "gbk4sdgsgrSFGlsdjkfet4rf=="]`}',
        "tool_call_id": "call_fqZHT1DNcil1pbIv6UbOWVq9",
        "name": "Zoom_ListUpcomingMeetings",
    },
    {
        "role": "assistant",
        "content": "The upcoming meetings are: 385572793583611134, 4388337744, 303948585686. You can join them on Zoom [here](https://zoom.us/j/385572793583611134), [here](https://zoom.us/j/4388337744), [here](https://zoom.us/j/303948585686).",
    },
]


@tool_eval()
def zoom_eval_suite() -> EvalSuite:
    """Create an evaluation suite for Zoom meeting tools."""
    suite = EvalSuite(
        name="Zoom Meeting Tools Evaluation",
        system_message="You are an AI assistant that can create and manage Zoom meetings using the provided tools.",
        catalog=catalog,
        rubric=rubric,
    )

    # List Upcoming Meetings Scenarios
    suite.add_case(
        name="List upcoming meetings",
        user_message="any meetings on the horizon?",
        expected_tool_calls=[
            (
                list_upcoming_meetings,
                {
                    "user_id": "me",
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="user_id", weight=1.0),
        ],
    )

    suite.add_case(
        name="Get meeting invitation",
        user_message="give me the invite to that meeting i think it might be 385572793583611134",
        expected_tool_calls=[
            (
                get_meeting_invitation,
                {
                    "meeting_id": 385572793583611134,
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="meeting_id", weight=1.0),
        ],
    )

    suite.add_case(
        name="Create instant meeting",
        user_message="""need a new meeting 'Discuss without action'.
The agenda for this meeting:
    1. What do we want to discuss?
    2. Don't do any real work, just discuss.
Only people with corporate.com emails can join, should be authenticated users only, I want a waiting room, and set meeting password to 'nine-to-five'. johndoe@corporate.com can be host if I can't make it. Oh, also, ensure joe@corporate.com and also jane@corporate.com are invited.""",
        expected_tool_calls=[
            (
                create_instant_meeting,
                {
                    "title": "Discuss without action",
                    "description": "1. What do we want to discuss?\n2. Don't do any real work, just discuss.",
                    "password": "nine-to-five",
                    "alternative_host_emails": ["johndoe@corporate.com"],
                    "authentication_domains": ["corporate.com"],
                    "meeting_authentication": True,
                    "attendee_email_addresses": ["joe@corporate.com", "jane@corporate.com"],
                    "waiting_room": True,
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="title", weight=0.1),
            SimilarityCritic(critic_field="description", weight=0.1, similarity_threshold=0.6),
            BinaryCritic(critic_field="password", weight=0.1),
            BinaryCritic(critic_field="alternative_host_emails", weight=0.1),
            BinaryCritic(critic_field="authentication_domains", weight=0.1),
            BinaryCritic(critic_field="meeting_authentication", weight=0.1),
            BinaryCritic(critic_field="attendee_email_addresses", weight=0.1),
            BinaryCritic(critic_field="waiting_room", weight=0.1),
        ],
    )

    suite.add_case(
        name="Get meeting summary",
        user_message="If there's any summary for rfk42tj34ewrDFk43f//234g3wgh== then let me know",
        expected_tool_calls=[
            (
                get_meeting_summary,
                {
                    "meeting_uuid": "rfk42tj34ewrDFk43f//234g3wgh==",
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="meeting_id", weight=1.0),
        ],
    )

    suite.add_case(
        name="Get meeting summary",
        user_message="Get the summary for each",
        expected_tool_calls=[
            (
                get_meeting_summary,
                {
                    "meeting_uuid": "rfk42tj34ewrDFk43f//234g3wgh==",
                },
            ),
            (
                get_meeting_summary,
                {
                    "meeting_uuid": "2343f2tj34ewrDF34g3wzq==",
                },
            ),
            (
                get_meeting_summary,
                {
                    "meeting_uuid": "gbk4sdgsgrSFGlsdjkfet4rf==",
                },
            ),
        ],
        critics=[
            BinaryCritic(critic_field="meeting_uuid", weight=1.0),
        ],
        additional_messages=list_upcoming_meetings_history,
    )

    return suite
