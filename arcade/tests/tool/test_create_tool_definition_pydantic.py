from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from arcade.sdk.schemas import (
    ToolOutput,
    ValueSchema,
)
from arcade.sdk.tool import tool
from arcade.tool.catalog import ToolCatalog


class ProductOutput(BaseModel):
    product_name: str = Field(..., description="The name of the product")
    price: int = Field(..., description="The price of the product")
    stock_quantity: int = Field(..., description="The stock quantity of the product")


@tool(desc="A function that returns a Pydantic model")
def func_returns_pydantic_model() -> Annotated[ProductOutput, "The product, price, and quantity"]:
    return ProductOutput(
        product_name="Product 1",
        price=100,
        stock_quantity=1000,
    )


# TODO: Function that takes a Pydantic model as an argument: break it down into components? Look at OpenAPI, do they represent nested arguments?
# TODO: Function that takes a Pydantic Field as an argument
# TODO: Pydantic Field() properties: description, default, title, default_factory, nullable
# TODO: Pydantic Field() properties stretch goal: gt, ge, lt, le, multiple_of, range, regex, max_length, min_length, max_items, min_items, unique_items, exclusive_maximum, exclusive_minimum


@pytest.mark.parametrize(
    "func_under_test, expected_tool_def_fields",
    [
        pytest.param(
            func_returns_pydantic_model,
            {
                "output": ToolOutput(
                    value_schema=ValueSchema(val_type="json", enum=None),
                    available_modes=["value", "error"],
                    description="The product, price, and quantity",
                )
            },
            id="func_returns_pydantic_model",
        ),
    ],
)
def test_create_tool_def(func_under_test, expected_tool_def_fields):
    tool_def = ToolCatalog.create_tool_definition(func_under_test, "1.0")

    assert tool_def.version == "1.0"

    for field, expected_value in expected_tool_def_fields.items():
        assert getattr(tool_def, field) == expected_value
