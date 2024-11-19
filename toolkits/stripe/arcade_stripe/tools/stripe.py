from typing import Annotated, Optional

from arcade.sdk import tool
from arcade_stripe.utils import get_stripe_api


@tool
def create_customer(
    name: Annotated[str, "The name of the customer."],
    email: Annotated[Optional[str], "The email of the customer."] = None,
) -> Annotated[str, "The created customer."]:
    """This tool will create a customer in Stripe."""
    stripe_api = get_stripe_api()
    return stripe_api.run(create_customer.__name__, name=name, email=email)


@tool
def list_customers(
    limit: Annotated[
        Optional[int],
        "A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 10.",
    ] = None,
    email: Annotated[
        Optional[str],
        "A case-sensitive filter on the list based on the customer's email field. The value must be a string.",
    ] = None,
) -> Annotated[str, "A list of customers."]:
    """This tool will fetch a list of Customers from Stripe."""
    stripe_api = get_stripe_api()
    return stripe_api.run(list_customers.__name__, limit=limit, email=email)


@tool
def create_product(
    name: Annotated[str, "The name of the product."],
    description: Annotated[Optional[str], "The description of the product."] = None,
) -> Annotated[str, "The created product."]:
    """This tool will create a product in Stripe."""
    stripe_api = get_stripe_api()
    return stripe_api.run(create_product.__name__, name=name, description=description)


@tool
def list_products(
    limit: Annotated[
        Optional[int],
        "A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 10.",
    ] = None,
) -> Annotated[str, "A list of products."]:
    """This tool will fetch a list of Products from Stripe."""
    stripe_api = get_stripe_api()
    return stripe_api.run(list_products.__name__, limit=limit)


@tool
def create_price(
    product: Annotated[str, "The ID of the product to create the price for."],
    unit_amount: Annotated[int, "The unit amount of the price in cents."],
    currency: Annotated[str, "The currency of the price."],
) -> Annotated[str, "The created price."]:
    """This tool will create a price in Stripe. If a product has not already been"""
    stripe_api = get_stripe_api()
    return stripe_api.run(
        create_price.__name__, product=product, unit_amount=unit_amount, currency=currency
    )


@tool
def list_prices(
    product: Annotated[Optional[str], "The ID of the product to list prices for."] = None,
    limit: Annotated[
        Optional[int],
        "A limit on the number of objects to be returned. Limit can range between 1 and 100, and the default is 10.",
    ] = None,
) -> Annotated[str, "A list of prices."]:
    """This tool will fetch a list of Prices from Stripe."""
    stripe_api = get_stripe_api()
    return stripe_api.run(list_prices.__name__, product=product, limit=limit)


@tool
def create_payment_link(
    price: Annotated[str, "The ID of the price to create the payment link for."],
    quantity: Annotated[int, "The quantity of the product to include."],
) -> Annotated[str, "The created payment link."]:
    """This tool will create a payment link in Stripe."""
    stripe_api = get_stripe_api()
    return stripe_api.run(create_payment_link.__name__, price=price, quantity=quantity)


@tool
def create_invoice(
    customer: Annotated[str, "The ID of the customer to create the invoice for."],
    days_until_due: Annotated[Optional[int], "The number of days until the invoice is due."] = None,
) -> Annotated[str, "The created invoice."]:
    """This tool will create an invoice in Stripe."""
    stripe_api = get_stripe_api()
    return stripe_api.run(create_invoice.__name__, customer=customer, days_until_due=days_until_due)


@tool
def create_invoice_item(
    customer: Annotated[str, "The ID of the customer to create the invoice item for."],
    price: Annotated[str, "The ID of the price for the item."],
    invoice: Annotated[str, "The ID of the invoice to create the item for."],
) -> Annotated[str, "The created invoice item."]:
    """This tool will create an invoice item in Stripe."""
    stripe_api = get_stripe_api()
    return stripe_api.run(
        create_invoice_item.__name__, customer=customer, price=price, invoice=invoice
    )


@tool
def finalize_invoice(
    invoice: Annotated[str, "The ID of the invoice to finalize."],
) -> Annotated[str, "The finalized invoice."]:
    """This tool will finalize an invoice in Stripe."""
    stripe_api = get_stripe_api()
    return stripe_api.run(finalize_invoice.__name__, invoice=invoice)


@tool
def retrieve_balance() -> Annotated[str, "The balance."]:
    """This tool will retrieve the balance from Stripe. It takes no input."""
    stripe_api = get_stripe_api()
    return stripe_api.run(
        retrieve_balance.__name__,
    )
