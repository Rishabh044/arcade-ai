from arcade_hubspot.tools.deals import set_deal_priority_for_contact

from arcade.sdk import ToolCatalog
from arcade.sdk.eval import (
    EvalRubric,
    EvalSuite,
    tool_eval,
)
from arcade.sdk.eval.critic import BinaryCritic, SimilarityCritic

# Evaluation rubric
rubric = EvalRubric(
    fail_threshold=0.9,
    warn_threshold=0.95,
)

catalog = ToolCatalog()
catalog.add_tool(set_deal_priority_for_contact, "HubSpot")


@tool_eval()
def hubspot_deal_eval_suite() -> EvalSuite:
    """Create an evaluation suite for HubSpot deal-related tools."""
    suite = EvalSuite(
        name="HubSpot Deal Tools Evaluation",
        system_message="You are an AI assistant that can manage HubSpot deals using the provided tools.",
        catalog=catalog,
        rubric=rubric,
    )

    suite.add_case(
        name="Set deal pr            iority to high",
        user_message="Fl     ag the deal as high prio for john.doe@example.com",
        expected_tool_calls=[
            (
                set_deal_priority_for_contact,
                {
                    "email": "john.doe@example.com",
                    "priority": "high",
                },
            )
        ],
        critics=[
            SimilarityCritic(critic_field="email", weight=0.5),
            BinaryCritic(critic_field="priority", weight=0.5),
        ],
    )

    suite.add_case(
        name="Set deal priority to medium",
        user_message="Change the deal priority to medium for jane.doe@example.com",
        expected_tool_calls=[
            (
                set_deal_priority_for_contact,
                {
                    "email": "jane.doe@example.com",
                    "priority": "medium",
                },
            )
        ],
        critics=[
            SimilarityCritic(critic_field="email", weight=0.5),
            BinaryCritic(critic_field="priority", weight=0.5),
        ],
    )

    suite.add_case(
        name="Set deal priority to low",
        user_message="Please set the deal priority to low for sally@example.com",
        expected_tool_calls=[
            (
                set_deal_priority_for_contact,
                {
                    "email": "sally@example.com",
                    "priority": "low",
                },
            )
        ],
        critics=[
            SimilarityCritic(critic_field="email", weight=0.5),
            BinaryCritic(critic_field="priority", weight=0.5),
        ],
    )

    return suite
