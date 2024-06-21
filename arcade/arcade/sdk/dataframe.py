
try:
    import pandas as pd
except ImportError:
    raise ImportError("Pandas is required for this SDK component. Please install it using `pip install pandas`.")

from typing import Any, Dict
from arcade.sdk.client import get_data, send_data


async def save_df(df: pd.DataFrame, name: str) -> Dict[str, Any]:
    """
    Asynchronously saves a DataFrame to the server by converting it to a dictionary and using the SDK's send_data function.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        name (str): The name under which the DataFrame should be saved.

    Returns:
        Dict[str, Any]: The server's response after saving the DataFrame.
    """
    data_dict = df.to_dict(orient='records')
    response = await send_data(name=name, data={"data": data_dict})
    return response


async def get_df(data_id: int) -> pd.DataFrame:
    """
    Asynchronously retrieves a DataFrame from the server using its data ID.

    Args:
        data_id (int): The unique identifier for the DataFrame to retrieve.

    Returns:
        pd.DataFrame: The DataFrame retrieved from the server.
    """
    response = await get_data(data_id=data_id)
    df = pd.DataFrame(response['data'])
    return df
