from arcade.sdk import ToolCatalog
from arcade.sdk.eval import (
    BinaryCritic,
    EvalRubric,
    EvalSuite,
    ExpectedToolCall,
    tool_eval,
)

import arcade_google
from arcade_google.tools.calendar import get_free_busy_time_slots
from arcade_google.tools.models import DateRange

rubric = EvalRubric(
    fail_threshold=0.9,
    warn_threshold=0.95,
)

catalog = ToolCatalog()
catalog.add_module(arcade_google)


@tool_eval()
def get_free_busy_eval_suite() -> EvalSuite:
    """Create an evaluation suite for free/busy slots Calendar tool."""
    suite = EvalSuite(
        name="Calendar Tools Evaluation",
        system_message=(
            "You are an AI assistant that can manage calendars and events using the provided tools. Today is 2024-09-26"
        ),
        catalog=catalog,
        rubric=rubric,
    )

    suite.add_case(
        name="Get free/busy slots for the next 5 days",
        user_message=("What are my free/busy slots for the next 5 days?"),
        expected_tool_calls=[
            ExpectedToolCall(
                func=get_free_busy_time_slots,
                args={
                    "additional_people_email_addresses": None,
                    "date_range": DateRange.NEXT_5_DAYS,
                    "start_date": None,
                    "end_date": None,
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="additional_people_email_addresses", weight=0.1),
            BinaryCritic(critic_field="date_range", weight=0.6),
            BinaryCritic(critic_field="start_date", weight=0.1),
            BinaryCritic(critic_field="end_date", weight=0.1),
        ],
    )

    suite.add_case(
        name="Get free/busy slots this week",
        user_message=("What are my free/busy slots for this week?"),
        expected_tool_calls=[
            ExpectedToolCall(
                func=get_free_busy_time_slots,
                args={
                    "additional_people_email_addresses": None,
                    "date_range": DateRange.THIS_WEEK,
                    "start_date": None,
                    "end_date": None,
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="additional_people_email_addresses", weight=0.1),
            BinaryCritic(critic_field="date_range", weight=0.6),
            BinaryCritic(critic_field="start_date", weight=0.1),
            BinaryCritic(critic_field="end_date", weight=0.1),
        ],
    )

    suite.add_case(
        name="Get free/busy slots today",
        user_message=("What times do I have free on my calendar today?"),
        expected_tool_calls=[
            ExpectedToolCall(
                func=get_free_busy_time_slots,
                args={
                    "additional_people_email_addresses": None,
                    "date_range": DateRange.TODAY,
                    "start_date": None,
                    "end_date": None,
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="additional_people_email_addresses", weight=0.1),
            BinaryCritic(critic_field="date_range", weight=0.6),
            BinaryCritic(critic_field="start_date", weight=0.1),
            BinaryCritic(critic_field="end_date", weight=0.1),
        ],
    )

    suite.add_case(
        name="Get free/busy slots for a specific email address",
        user_message=("Is johndoe@example.com free some time tomorrow?"),
        expected_tool_calls=[
            ExpectedToolCall(
                func=get_free_busy_time_slots,
                args={
                    "additional_people_email_addresses": ["johndoe@example.com"],
                    "date_range": DateRange.TOMORROW,
                    "start_date": None,
                    "end_date": None,
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="date_range", weight=0.35),
            BinaryCritic(critic_field="additional_people_email_addresses", weight=0.35),
            BinaryCritic(critic_field="start_date", weight=0.15),
            BinaryCritic(critic_field="end_date", weight=0.15),
        ],
    )

    suite.add_case(
        name="Get free/busy slots for a specific date range",
        user_message=("What are my free/busy slots between 2024-09-27 and 2024-09-29?"),
        expected_tool_calls=[
            ExpectedToolCall(
                func=get_free_busy_time_slots,
                args={
                    "additional_people_email_addresses": None,
                    "date_range": None,
                    "start_date": "2024-09-27",
                    "end_date": "2024-09-29",
                },
            )
        ],
        critics=[
            BinaryCritic(critic_field="additional_people_email_addresses", weight=0.10),
            BinaryCritic(critic_field="date_range", weight=0.30),
            BinaryCritic(critic_field="start_date", weight=0.30),
            BinaryCritic(critic_field="end_date", weight=0.30),
        ],
    )

    return suite
