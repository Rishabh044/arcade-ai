import pandas as pd
from typing import Annotated, Literal, Optional, Union
from arcade.sdk.tool import tool


def get_people_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [25, 30, 35, 40, 45],
            "gender": ["F", "M", "M", "M", "F"],
            "role": ["Engineer", "Manager", "Director", "VP", "CEO"],
            "department": [
                "Engineering",
                "Management",
                "Management",
                "Management",
                "Management",
            ],
            "salary": [1000, 2000, 3000, 4000, 5000],
            "bonus": [100, 200, 300, 400, 500],
            "start_date": [
                "2021-01-01",
                "2020-01-01",
                "2019-01-01",
                "2018-01-01",
                "2017-01-01",
            ],
        }
    )


PeopleRecord = list[dict[str, Union[str, int]]]


@tool
async def search_employee(
    name: Annotated[Optional[str], "Name of the employee"] = None,
    role: Annotated[
        Literal["Engineer", "Manager", "Director"] | None, "Role of the employee"
    ] = None,
    limit: Annotated[int, "Number of employees to return"] = 5,
) -> Annotated[PeopleRecord, "The JSON list of employees matching the search"]:
    """Search for an employee by name or role."""
    df = get_people_df()
    if name:
        df = df[df["name"] == name]
    if role:
        df = df[df["role"] == role]

    df = df.head(limit)

    # return employees by record
    return df.to_dict(orient="records")
