import arcade_stripe
from arcade_stripe.tools.stripe import (
    create_customer,
    create_invoice,
    create_invoice_item,
    create_payment_link,
    create_price,
    create_product,
    finalize_invoice,
    list_customers,
    list_prices,
    list_products,
    retrieve_balance,
)

from arcade.sdk import ToolCatalog
from arcade.sdk.eval import (
    EvalRubric,
    EvalSuite,
    tool_eval,
)
from arcade.sdk.eval.critic import BinaryCritic, SimilarityCritic

# Evaluation rubric
rubric = EvalRubric(
    fail_threshold=0.85,
    warn_threshold=0.95,
)


catalog = ToolCatalog()
catalog.add_module(arcade_stripe)


@tool_eval()
def stripe_eval_suite():
    suite = EvalSuite(
        name="stripe Tools Evaluation",
        system_message="You are an AI assistant with access to stripe tools. Use them to help the user with their tasks.",
        catalog=catalog,
        rubric=rubric,
    )

    suite.add_case(
        name="Create a customer",
        user_message="Create a customer her name is Jennifer. Contact info is j3nnifer998332111123@example.com",
        expected_tool_calls=[
            (
                create_customer,
                {
                    "name": "Jennifer",
                    "email": "j3nnifer998332111123@example.com",
                },
            )
        ],
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="name", weight=0.5),
            BinaryCritic(critic_field="email", weight=0.5),
        ],
    )

    suite.add_case(
        name="List customers",
        user_message="List all customers up to 5",
        expected_tool_calls=[
            (
                list_customers,
                {
                    "limit": 5,
                },
            )
        ],
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="limit", weight=1.0),
        ],
    )

    suite.add_case(
        name="Create a product",
        user_message="Create a product called Gadget which is a useful GPS gadget.",
        expected_tool_calls=[
            (
                create_product,
                {
                    "name": "Gadget",
                    "description": "A useful GPS gadget.",
                },
            )
        ],
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="name", weight=0.5),
            SimilarityCritic(critic_field="description", weight=0.5, similarity_threshold=0.8),
        ],
    )

    suite.add_case(
        name="List products",
        user_message="List all products with a max of 5",
        expected_tool_calls=[
            (
                list_products,
                {
                    "limit": 5,
                },
            )
        ],
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="limit", weight=1.0),
        ],
    )

    suite.add_case(
        name="Create a price",
        user_message="List product 239823745987sefg34 for 10 bucks USD",
        expected_tool_calls=[
            (
                create_price,
                {
                    "product": "239823745987sefg34",
                    "unit_amount": 10,
                    "currency": "USD",
                },
            )
        ],
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="product", weight=0.33),
            BinaryCritic(critic_field="unit_amount", weight=0.33),
            BinaryCritic(critic_field="currency", weight=0.34),
        ],
    )

    suite.add_case(
        name="List prices",
        user_message="show me all prices up to 5",
        expected_tool_calls=[
            (
                list_prices,
                {
                    "limit": 5,
                },
            )
        ],
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="limit", weight=1.0),
        ],
    )

    suite.add_case(
        name="Create a payment link",
        user_message="Make a payment link for product 443tfgeb353 w/ quantity 2",
        expected_tool_calls=[
            (
                create_payment_link,
                {
                    "price": "price_123",
                    "quantity": 2,
                },
            )
        ],
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="price", weight=0.5),
            BinaryCritic(critic_field="quantity", weight=0.5),
        ],
    )

    suite.add_case(
        name="Create an invoice",
        user_message="Create an invoice for customer 'cust_123' due in 30 days",
        expected_tool_calls=[
            (
                create_invoice,
                {
                    "customer": "cust_123",
                    "days_until_due": 30,
                },
            )
        ],
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="customer", weight=0.5),
            BinaryCritic(critic_field="days_until_due", weight=0.5),
        ],
    )

    suite.add_case(
        name="Create an invoice item",
        user_message="Create an invoice item for customer cust_1344343523 with price price_12434523 on invoice inv_123",
        expected_tool_calls=[
            (
                create_invoice_item,
                {
                    "customer": "cust_1344343523",
                    "price": "price_12434523",
                    "invoice": "inv_123",
                },
            )
        ],
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="customer", weight=0.33),
            BinaryCritic(critic_field="price", weight=0.33),
            BinaryCritic(critic_field="invoice", weight=0.34),
        ],
    )

    suite.add_case(
        name="Finalize an invoice",
        user_message="Complete invoice 'inv_122213344ddff23'",
        expected_tool_calls=[
            (
                finalize_invoice,
                {
                    "invoice": "inv_122213344ddff23",
                },
            )
        ],
        rubric=rubric,
        critics=[
            BinaryCritic(critic_field="invoice", weight=1.0),
        ],
    )

    suite.add_case(
        name="Retrieve balance",
        user_message="What's my balance?",
        expected_tool_calls=[(retrieve_balance, {})],
        rubric=rubric,
        critics=[],
    )

    return suite
