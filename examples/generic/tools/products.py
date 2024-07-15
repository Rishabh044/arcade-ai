from typing import Union, Annotated, Literal
from arcade.sdk.tool import tool, get_secret
import pandas as pd
from pydantic import BaseModel, Field


class ProductFilter(BaseModel):
    column: str = Field(..., description="The column to filter on")


class FilterRating(ProductFilter):
    greater_than: int = Field(
        ..., description="The rating to filter greater than", gt=0, lt=5
    )


class FilterPriceGreaterThan(ProductFilter):
    price: int = Field(..., description="The price to filter greater than", gt=0)


class FilterPriceLessThan(ProductFilter):
    price: int = Field(..., description="The price to filter less than", gt=0)


class ProductSearch(BaseModel):
    """The search action to perform"""

    column: str = Field("Product Name", description="The column to search in")
    """the column to search in"""

    query: str = Field(..., description="The query to search for")
    """the query to search for"""

    filter_operation: Union[
        FilterRating, FilterPriceGreaterThan, FilterPriceLessThan
    ] = None
    """The filter operation to perform"""


class ProductOutput(BaseModel):
    product_name: str = Field(..., description="The name of the product")
    price: int = Field(..., description="The price of the product")
    stock_quantity: int = Field(..., description="The stock quantity of the product")


@tool
def read_products(
    action: Annotated[ProductSearch, "The search action to perform"],
    cols: Annotated[
        Literal["Product Name", "Price", "Stock Quantity"], "The columns to return"
    ] = ["Product Name", "Price", "Stock Quantity"],
) -> Annotated[list[ProductOutput], "The list of products matching the search"]:
    """Used to search through products by name and filter by rating or price."""

    file_path = get_secret(
        "PRODUCTS_PATH",
        "/Users/spartee/Dropbox/Arcade/platform/toolserver/examples/data/Sample_Products_Info.csv",
    )
    try:
        df = pd.read_csv(file_path)
        df = df[cols]

        if action.filter_operation:
            if isinstance(action.filter_operation, FilterRating):
                df = df[
                    df[action.filter_operation.column]
                    > action.filter_operation.greater_than
                ]
            elif isinstance(action.filter_operation, FilterPriceGreaterThan):
                df = df[
                    df[action.filter_operation.column] > action.filter_operation.price
                ]
            elif isinstance(action.filter_operation, FilterPriceLessThan):
                df = df[
                    df[action.filter_operation.column] < action.filter_operation.price
                ]

    except Exception as e:
        # TODO what to do here?
        print(e)
    return df.to_json()
