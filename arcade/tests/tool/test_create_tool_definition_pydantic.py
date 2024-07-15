from typing import Annotated, Optional

import pytest
from pydantic import BaseModel, Field

from arcade.sdk.schemas import (
    InputParameter,
    ToolInputs,
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


# TODO: Pydantic Field() properties: default, default_factory
@tool(desc="A function that accepts a required Pydantic Field with a description")
def func_takes_pydantic_field_with_description(
    product_name: str = Field(..., description="The name of the product"),
) -> str:
    return product_name


@tool(desc="A function that accepts an optional Pydantic Field")
def func_takes_pydantic_field_optional(
    product_name: str = Field(None, description="The name of the product"),
) -> str:
    return product_name


@tool(desc="A function that accepts an Pydantic Field")
def func_takes_pydantic_field_optional_annotation(
    product_name: Optional[str] = Field(description="The name of the product"),
) -> str:
    return product_name


# Annotated[] takes precedence over Field() properties
@tool(desc="A function that accepts an annotated Pydantic Field")
def func_takes_pydantic_field_annotated_description(
    product_name: Annotated[str, "The name of the product"] = Field(
        ..., description="The name of the product???"
    ),
) -> str:
    return product_name


# Annotated[] takes precedence over Field() properties
@tool(desc="A function that accepts an annotated Pydantic Field")
def func_takes_pydantic_field_annotated_name_and_description(
    product_name: Annotated[str, "ProductName", "The name of the product"] = Field(
        ..., title="The name of the product???"
    ),
) -> str:
    return product_name


# TODO: Function that takes a Pydantic model as an argument: break it down into components? Look at OpenAPI, do they represent nested arguments?
# TODO: Should title and default_value be added to JSON schema?
# TODO: Pydantic Field() properties stretch goal: gt, ge, lt, le, multiple_of, range, regex, max_length, min_length, max_items, min_items, unique_items, exclusive_maximum, exclusive_minimum, title


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
        pytest.param(
            func_takes_pydantic_field_with_description,
            {
                "inputs": ToolInputs(
                    parameters=[
                        InputParameter(
                            name="product_name",
                            description="The name of the product",
                            required=True,
                            inferrable=True,
                            value_schema=ValueSchema(val_type="string", enum=None),
                        )
                    ]
                )
            },
        ),
        pytest.param(
            func_takes_pydantic_field_optional,
            {
                "inputs": ToolInputs(
                    parameters=[
                        InputParameter(
                            name="product_name",
                            description="The name of the product",
                            required=False,
                            inferrable=True,
                            value_schema=ValueSchema(val_type="string", enum=None),
                        )
                    ]
                )
            },
        ),
        pytest.param(
            func_takes_pydantic_field_optional_annotation,
            {
                "inputs": ToolInputs(
                    parameters=[
                        InputParameter(
                            name="product_name",
                            description="The name of the product",
                            required=False,
                            inferrable=True,
                            value_schema=ValueSchema(val_type="string", enum=None),
                        )
                    ]
                )
            },
        ),
        pytest.param(
            func_takes_pydantic_field_annotated_description,
            {
                "inputs": ToolInputs(
                    parameters=[
                        InputParameter(
                            name="product_name",
                            description="The name of the product",  # Annotated[] takes precedence over Field() properties
                            required=True,
                            inferrable=True,
                            value_schema=ValueSchema(val_type="string", enum=None),
                        )
                    ]
                )
            },
        ),
        pytest.param(
            func_takes_pydantic_field_annotated_name_and_description,
            {
                "inputs": ToolInputs(
                    parameters=[
                        InputParameter(
                            name="ProductName",
                            description="The name of the product",  # Annotated[] takes precedence over Field() properties
                            required=True,
                            inferrable=True,
                            value_schema=ValueSchema(val_type="string", enum=None),
                        )
                    ]
                )
            },
        ),
    ],
)
def test_create_tool_def(func_under_test, expected_tool_def_fields):
    tool_def = ToolCatalog.create_tool_definition(func_under_test, "1.0")

    assert tool_def.version == "1.0"

    for field, expected_value in expected_tool_def_fields.items():
        assert getattr(tool_def, field) == expected_value
