
import os
import json
import httpx

from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from enum import Enum


class HttpClient:
    """
    A simple HTTP client class to handle requests to a specified base URL with optional authentication.
    """
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        """
        Initializes the HttpClient with a base URL and an optional authentication token.

        Args:
            base_url (str): The base URL for the HTTP requests.
            auth_token (Optional[str]): Optional bearer token for authorization.
        """
        self.base_url = base_url
        self.auth_token = auth_token
        self.client = httpx.AsyncClient()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def post(self, endpoint: str, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None) -> Any:
        """
        Sends a POST request to the specified endpoint with the provided data and files.

        Args:
            endpoint (str): The endpoint to send the POST request to.
            data (Dict[str, Any]): The data to send in the POST request.
            files (Optional[Dict[str, Any]]): Optional files to send with the request.

        Returns:
            Any: The JSON response from the server.
        """
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        try:
            if files:
                response = await self.client.post(f"{self.base_url}{endpoint}", files=files, headers=headers)
            else:
                response = await self.client.post(f"{self.base_url}{endpoint}", json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP error occurred: {e.response.status_code}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Request error occurred: {e}")

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Sends a GET request to the specified endpoint with optional parameters.

        Args:
            endpoint (str): The endpoint to send the GET request to.
            params (Optional[Dict[str, Any]]): Optional parameters to include in the request.

        Returns:
            Any: The JSON response from the server.
        """
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}
        try:
            response = await self.client.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP error occurred: {e.response.status_code}")
        except httpx.RequestError as e:
            raise RuntimeError(f"Request error occurred: {e}")

@asynccontextmanager
async def managed_http_client(base_url: str, auth_token: Optional[str] = None):
    """
    Context manager to handle the lifecycle of HttpClient instances.

    Args:
        base_url (str): The base URL for the HTTP requests.
        auth_token (Optional[str]): Optional bearer token for authorization.
    """
    client = HttpClient(base_url, auth_token)
    try:
        yield client
    finally:
        await client.__aexit__(None, None, None)

def get_base_url() -> str:
    return os.getenv('TOOLSERVE_URL', 'http://localhost:8000')


# ----- SDK Functions -----


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

async def log(message: str = "", level: LogLevel = LogLevel.INFO, auth_token: Optional[str] = None, endpoint: str = "/api/v1/log"):
    """
    Asynchronously sends a log message to a specified endpoint.

    This function constructs a log entry with a message and a log level, then sends it to the server using the provided endpoint. It uses an HTTP POST request within a managed HTTP client context.

    Args:
        message (str): The log message to send. Defaults to an empty string.
        level (LogLevel): The severity level of the log message. Defaults to LogLevel.INFO.
        auth_token (Optional[str]): An optional authorization token for the request.
        endpoint (str): The API endpoint to which the log message is sent. Defaults to "/api/v1/log".

    Returns:
        Any: The response from the server as a result of the log message post request.
    """
    base_url = get_base_url()
    if isinstance(level, str):
        level = LogLevel(level)
    async with managed_http_client(base_url, auth_token) as client:
        log_data = {"msg": message, "level": level.value}
        return await client.post(endpoint, data=log_data)


async def list_data(auth_token: Optional[str] = None, endpoint: str = "/api/v1/data") -> List[Dict[str, Any]]:
    """
    Retrieve a list of data objects from a specified endpoint.

    Args:
        auth_token (Optional[str]): Optional authorization token.
        endpoint (str): API endpoint to send the request to. Defaults to "/api/v1/data".

    Returns:
        Dict[str, Any]: The deserialized JSON data retrieved from the server.
    """
    base_url = get_base_url()
    async with managed_http_client(base_url, auth_token) as client:
        response = await client.get(endpoint)
    return response["data"]

async def get_data(data_id: int, auth_token: Optional[str] = None, endpoint: str = "/api/v1/data/object") -> Any:
    """
    Retrieve data object by its primary key from a specified endpoint.

    Args:
        data_id (int): The primary key of the data object to retrieve.
        auth_token (Optional[str]): Optional authorization token.
        endpoint (str): API endpoint to send the request to. Defaults to "/api/v1/data/object".

    Returns:
        Any: The deserialized JSON data retrieved from the server.
    """
    base_url = get_base_url()
    endpoint = f"{endpoint}/{str(data_id)}"  # Append the data ID to the endpoint URL
    async with managed_http_client(base_url, auth_token) as client:
        response = await client.get(endpoint)
    json_blob = response["data"].get('json_blob', '{}')
    return json.loads(json_blob)


async def send_data(name: str, data: Dict[str, Any], auth_token: Optional[str] = None, endpoint: str = "/api/v1/data") -> Dict[str, Any]:
    """
    Send data to a specified endpoint, serializing the data into JSON under the key 'json_blob'.

    Args:
        data (Dict[str, Any]): Data to be serialized and sent.
        auth_token (Optional[str]): Optional authorization token.
        endpoint (str): API endpoint to send the data to.

    Returns:
        Dict[str, Any]: The response from the server after sending the data.
    """
    base_url = get_base_url()
    json_blob = json.dumps(data)
    payload = {'file_name': name, 'json_blob': json_blob}
    async with managed_http_client(base_url, auth_token) as client:
        response = await client.post(endpoint, data=payload)
    if response["code"] != 200:
        raise RuntimeError(f"Failed to send data: {response['msg']}")
    else:
        return {
            "id": response["data"]["id"],
            "file_path": response["data"]["file_path"]
        }


async def save_artifact_from_file(file_path: str = "", auth_token: Optional[str] = None, endpoint: str = "/api/v1/artifact"):
    base_url = get_base_url()
    async with managed_http_client(base_url, auth_token) as client:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            return await client.post(endpoint, data={}, files=files)



