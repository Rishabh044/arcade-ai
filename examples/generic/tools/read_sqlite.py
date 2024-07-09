from typing import List

from arcade.sdk import Param, tool, get_secret
import pandas as pd

from sqlite3 import connect


@tool
async def read_sqlite(
    file_path: Param(str, "Path to the SQLite database file"),
    table_name: Param(str, "Name of the table to read from"),
    cols: Param(str, "Columns to read from the table") = "*",
) -> Param(str, "JSON of the dataframe holding the data from the table"):
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


@tool
def read_products(
    cols: Param(List[str], "Columns to read from the table") = [
        "Product Name",
        "Price",
        "Stock Quantity",
    ],
) -> Param(str, "JSON of the dataframe holding the data from the CSV file"):
    """Read data from a CSV file and save it as a DataFrame."""

    file_path = get_secret(
        "PRODUCTS_PATH",
        "/Users/spartee/Dropbox/Arcade/platform/toolserver/examples/data/Sample_Products_Info.csv",
    )
    try:
        df = pd.read_csv(file_path)
        df = df[cols]
    except Exception as e:
        print(e)
    return df.to_json()
