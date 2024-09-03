from arcade_slack.tools.chat import send_dm_to_user, send_message_to_channel

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


@tool_eval("gpt-3.5-turbo")
def slack_eval_suite() -> EvalSuite:
    """Create an evaluation suite for Slack messaging tools."""
    suite = EvalSuite(
        name="Slack Messaging Tools Evaluation",
        system="You are an AI assistant to a number of tools.",
    )

    # Register the Slack tools
    suite.register_tool(send_dm_to_user)
    suite.register_tool(send_message_to_channel)

    # Send DM to User Scenarios
    suite.add_case(
        name="Send DM to user with clear username",
        user_message="Send a direct message to johndoe saying 'Hello, can we meet at 3 PM?'",
        expected_tool="SendDmToUser",
        expected_tool_args={
            "user_name": "johndoe",
            "message": "Hello, can we meet at 3 PM?",
        },
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="user_name", weight=0.5),
            SimilarityCritic(critic_field="message", weight=0.5),
        ],
    )

    suite.add_case(
        name="Send DM with ambiguous username",
        user_message="Message John about the project deadline",
        expected_tool="SendDmToUser",
        expected_tool_args={
            "user_name": "john",
            "message": "Hi John, I wanted to check about the project deadline. Can you provide an update?",
        },
        rubric=rubric,
        critics=[
            SimilarityCritic(critic_field="user_name", weight=0.4),
            SimilarityCritic(critic_field="message", weight=0.6),
        ],
    )

    suite.add_case(
        name="Send DM with username in different format",
        user_message="DM Jane.Doe to reschedule our meeting",
        expected_tool="SendDmToUser",
        expected_tool_args={
            "user_name": "jane.doe",
            "message": "Hi Jane, I need to reschedule our meeting. When are you available?",
        },
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="user_name", weight=0.5),
            SimilarityCritic(critic_field="message", weight=0.5),
        ],
    )

    # Send Message to Channel Scenarios
    suite.add_case(
        name="Send message to channel with clear name",
        user_message="Post 'The new feature is now live!' in the #announcements channel",
        expected_tool="SendMessageToChannel",
        expected_tool_args={
            "channel_name": "announcements",
            "message": "The new feature is now live!",
        },
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="channel_name", weight=0.5),
            SimilarityCritic(critic_field="message", weight=0.5),
        ],
    )

    suite.add_case(
        name="Send message to channel with ambiguous name",
        user_message="Inform the engineering team about the upcoming maintenance in the general channel",
        expected_tool="SendMessageToChannel",
        expected_tool_args={
            "channel_name": "engineering",
            "message": "Attention team: There will be upcoming maintenance. Please save your work and expect some downtime.",
        },
        rubric=rubric,
        critics=[
            SimilarityCritic(critic_field="channel_name", weight=0.4),
            SimilarityCritic(critic_field="message", weight=0.6),
        ],
    )

    # Adversarial Scenarios
    suite.add_case(
        name="Ambiguous between DM and channel message",
        user_message="Send 'Great job on the presentation!' to the team",
        expected_tool="SendMessageToChannel",
        expected_tool_args={
            "channel_name": "general",
            "message": "Great job on the presentation!",
        },
        rubric=rubric,
        critics=[
            SimilarityCritic(critic_field="channel_name", weight=0.4),
            SimilarityCritic(critic_field="message", weight=0.6),
        ],
    )

    # TODO handle parallel tool calls better in eval
    suite.add_case(
        name="Multiple recipients in DM request",
        user_message="Send a DM to Alice and Bob about the meeting tomorrow",
        expected_tool="SendDmToUser",
        expected_tool_args={
            "user_name": "alice",
            "message": "Hi Alice, I'm sending a separate message to Bob as well. About our meeting tomorrow, [insert details here].",
        },
        rubric=rubric,
        critics=[
            SimilarityCritic(critic_field="user_name", weight=0.4),
            SimilarityCritic(critic_field="message", weight=0.6),
        ],
    )

    suite.add_case(
        name="Channel name similar to username",
        user_message="Post 'sounds great!' in john-project channel",
        expected_tool="SendMessageToChannel",
        expected_tool_args={
            "channel_name": "john-project",
            "message": "Sounds great!",
        },
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="channel_name", weight=0.5),
            SimilarityCritic(critic_field="message", weight=0.5),
        ],
    )

    return suite
