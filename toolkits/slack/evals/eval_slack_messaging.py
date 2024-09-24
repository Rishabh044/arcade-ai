from arcade.core.schema import ToolContext
from arcade.core.toolkit import Toolkit
import arcade_slack
from arcade_slack.tools.chat import send_dm_to_user, send_message_to_channel

from arcade.core.catalog import ToolCatalog
from arcade.sdk.eval import (
    BinaryCritic,
    EvalRubric,
    EvalSuite,
    ExpectedToolCall,
    SimilarityCritic,
    tool_eval,
)

# Evaluation rubric
rubric = EvalRubric(
    fail_threshold=0.8,
    warn_threshold=0.9,
)


catalog = ToolCatalog()
catalog.add_toolkit(Toolkit.from_module(arcade_slack))


@tool_eval()
def slack_eval_suite() -> EvalSuite:
    """Create an evaluation suite for Slack messaging tools."""
    suite = EvalSuite(
        name="Slack Messaging Tools Evaluation",
        system_message="You are an AI assistant that can send direct messages and post messages to channels in Slack using the provided tools.",
        catalog=catalog,
        rubric=rubric,
    )

    # Send DM to User Scenarios
    suite.add_case(
        name="Send DM to user with clear username",
        user_message="Send a direct message to johndoe saying 'Hello, can we meet at 3 PM?'",
        expected_tool_calls=[
            ExpectedToolCall(
                lambda: send_dm_to_user(
                    ToolContext(), "johndoe", "Hello, can we meet at 3 PM?"
                )
            )
        ],
        critics=[
            BinaryCritic(critic_field="user_name", weight=0.5),
            SimilarityCritic(critic_field="message", weight=0.5),
        ],
    )

    suite.add_case(
        name="Send DM with ambiguous username",
        user_message="Message John about the project deadline",
        expected_tool_calls=[
            ExpectedToolCall(
                lambda: send_dm_to_user(
                    ToolContext(),
                    "john",
                    "Hi John, I wanted to check about the project deadline. Can you provide an update?",
                )
            )
        ],
        critics=[
            SimilarityCritic(critic_field="user_name", weight=0.6),
            SimilarityCritic(critic_field="message", weight=0.4),
        ],
    )

    suite.add_case(
        name="Send DM with username in different format",
        user_message="DM Jane.Doe to reschedule our meeting",
        expected_tool_calls=[
            ExpectedToolCall(
                lambda: send_dm_to_user(
                    ToolContext(),
                    "jane.doe",
                    "Hi Jane, I need to reschedule our meeting. When are you available?",
                )
            )
        ],
        critics=[
            BinaryCritic(critic_field="user_name", weight=0.6),
            SimilarityCritic(critic_field="message", weight=0.4),
        ],
    )

    # Send Message to Channel Scenarios
    suite.add_case(
        name="Send message to channel with clear name",
        user_message="Post 'The new feature is now live!' in the #announcements channel",
        expected_tool_calls=[
            ExpectedToolCall(
                lambda: send_message_to_channel(
                    ToolContext(), "announcements", "The new feature is now live!"
                )
            )
        ],
        critics=[
            BinaryCritic(critic_field="channel_name", weight=0.6),
            SimilarityCritic(critic_field="message", weight=0.4),
        ],
    )

    suite.add_case(
        name="Send message to channel with ambiguous name",
        user_message="Inform the engineering team about the upcoming maintenance in the general channel",
        expected_tool_calls=[
            ExpectedToolCall(
                lambda: send_message_to_channel(
                    ToolContext(),
                    "engineering",
                    "Attention team: There will be upcoming maintenance. Please save your work and expect some downtime.",
                )
            )
        ],
        critics=[
            SimilarityCritic(critic_field="channel_name", weight=0.4),
            SimilarityCritic(critic_field="message", weight=0.6),
        ],
    )

    # Adversarial Scenarios
    suite.add_case(
        name="Ambiguous between DM and channel message",
        user_message="Send 'Great job on the presentation!' to the team",
        expected_tool_calls=[
            ExpectedToolCall(
                lambda: send_message_to_channel(
                    ToolContext(), "general", "Great job on the presentation!"
                )
            )
        ],
        critics=[
            SimilarityCritic(critic_field="channel_name", weight=0.4),
            SimilarityCritic(critic_field="message", weight=0.6),
        ],
    )

    # Multiple recipients in DM request
    suite.add_case(
        name="Multiple recipients in DM request",
        user_message="Send a DM to Alice and Bob about pushing the meeting tomorrow. I have to much work to do.",
        expected_tool_calls=[
            ExpectedToolCall(
                lambda: send_dm_to_user(
                    ToolContext(),
                    "alice",
                    "Hi Alice, about our meeting tomorrow, let's reschedule? I am swamped with work.",
                )
            ),
            ExpectedToolCall(
                lambda: send_dm_to_user(
                    ToolContext(),
                    "bob",
                    "Hi Bob, about our meeting tomorrow, let's reschedule? I am swamped with work.",
                )
            ),
        ],
        critics=[
            SimilarityCritic(critic_field="user_name", weight=0.6),
            SimilarityCritic(
                critic_field="message", weight=0.4, similarity_threshold=0.7
            ),
        ],
    )

    suite.add_case(
        name="Channel name similar to username",
        user_message="Post 'sounds great!' in john-project channel",
        expected_tool_calls=[
            ExpectedToolCall(
                lambda: send_message_to_channel(
                    ToolContext(), "john-project", "Sounds great!"
                )
            )
        ],
        critics=[
            BinaryCritic(critic_field="channel_name", weight=0.5),
            SimilarityCritic(critic_field="message", weight=0.5),
        ],
    )

    return suite
