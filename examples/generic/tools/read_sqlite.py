from typing import Annotated

from arcade.sdk.tool import tool
import pandas as pd

from sqlite3 import connect


@tool
async def read_sqlite(
    file_path: Annotated[str, "Path to the SQLite database file"],
    table_name: Annotated[str, "Name of the table to read from"],
    cols: Annotated[str, "Columns to read from the table"] = "*",
) -> str:
    """Read data from a SQLite database table and save it as a DataFrame.

    Columns to choose from are:
    - *: All columns
    - column_name: Single column
    - column_name1, column_name2, ...: Multiple columns
    """
    # Connect to the SQLite database
    conn = connect(file_path)
    cursor = conn.cursor()

    # Read the data from the table
    query = f"SELECT * FROM {table_name}"
    cursor.execute(query)
    rows = cursor.fetchall()

    # Get the column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]

    # Create a DataFrame from the data
    df = pd.DataFrame(rows, columns=columns)

    return df.json()
