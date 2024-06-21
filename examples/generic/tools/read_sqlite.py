
from arcade.sdk import Param, tool, get_secret
from arcade.sdk.dataframe import save_df
import pandas as pd

from sqlite3 import connect

@tool
async def read_sqlite(
    file_path: Param(str, "Path to the SQLite database file"),
    table_name: Param(str, "Name of the table to read from"),
    output_name: Param(str, "Name of the output data to save"),
    ) -> Param(str, "Output data name"):
    """Read data from a SQLite database table and save it as a DataFrame.

    Args:
        file_path (str): Path to the SQLite database file.
        table_name (str): Name of the table to read from.
        output_name (str): Name of the output data to save.

    Returns:
        str: Name of the output data.
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

    # Save the DataFrame
    await save_df(df, output_name)

    return output_name