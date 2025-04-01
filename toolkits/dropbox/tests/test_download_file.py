import json
from unittest.mock import MagicMock

import httpx
import pytest

from arcade_dropbox.tools.files import download_file
from arcade_dropbox.utils import clean_dropbox_entry


@pytest.fixture
def file_content_response_header():
    return json.dumps({
        "id": "123",
        "name": "test.txt",
        "path_display": "/test.txt",
        "size": 1024,
        "server_modified": "2021-01-01T00:00:00Z",
        "content_hash": "1234567890",
        "is_downloadable": True,
        "rev": "a1c10ce0dd78",
        "sharing_info": {
            "modified_by": "dbid:AAH4f99T0taONIb-OurWxbNQ6ywGRopQngc",
            "parent_shared_folder_id": "84528192421",
            "read_only": True,
        },
    })


@pytest.mark.asyncio
async def test_download_file_success(
    mock_context,
    mock_httpx_client,
    file_content_response_header,
):
    file_content = "test file content"

    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.side_effect = ValueError("not json")
    mock_httpx_response.headers = {"Dropbox-API-Result": file_content_response_header}
    mock_httpx_response.text = file_content

    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await download_file(
        context=mock_context,
        file_path="test.txt",
    )

    expected_response = clean_dropbox_entry(json.loads(file_content_response_header))
    expected_response["content"] = file_content
    expected_response["type"] = "file"

    assert tool_response == {"file": expected_response}


@pytest.mark.asyncio
async def test_download_file_path_not_found(
    mock_context,
    mock_httpx_client,
):
    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 409
    mock_httpx_response.json.return_value = {"error_summary": "path/not_found"}

    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await download_file(
        context=mock_context,
        file_path="test.txt",
    )

    assert tool_response == {
        "error": "The specified path was not found by Dropbox",
    }


@pytest.mark.asyncio
async def test_download_file_unsupported_file(
    mock_context,
    mock_httpx_client,
):
    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 409
    mock_httpx_response.json.return_value = {"error_summary": "unsupported_file/not_supported"}

    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await download_file(
        context=mock_context,
        file_path="test.txt",
    )

    assert tool_response == {
        "error": "The specified file is not supported for the requested operation",
    }


@pytest.mark.asyncio
async def test_download_file_server_error(
    mock_context,
    mock_httpx_client,
):
    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 500
    mock_httpx_response.text = "500 Internal server error"
    mock_httpx_response.json.side_effect = ValueError("not json")

    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await download_file(
        context=mock_context,
        file_path="test.txt",
    )

    assert tool_response == {
        "error": "500 Internal server error",
    }
