from unittest.mock import MagicMock

import httpx
import pytest

from arcade_dropbox.tools.browse import list_items_in_folder
from arcade_dropbox.utils import clean_dropbox_entries


@pytest.mark.asyncio
async def test_list_items_success_empty_folder(
    mock_context,
    mock_httpx_client,
):
    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {"entries": [], "cursor": None, "has_more": False}
    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await list_items_in_folder(
        context=mock_context,
        folder_path="/path/to/folder",
    )

    assert tool_response == {
        "items": [],
        "cursor": None,
        "has_more": False,
    }


@pytest.mark.asyncio
async def test_list_items_success_with_folder_entries(
    mock_context,
    mock_httpx_client,
    sample_folder_entry,
    sample_file_entry,
):
    entries = [sample_folder_entry, sample_file_entry]

    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {"entries": entries, "cursor": None, "has_more": False}
    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await list_items_in_folder(
        context=mock_context,
        folder_path="/path/to/folder",
    )

    assert tool_response == {
        "items": clean_dropbox_entries(entries),
        "cursor": None,
        "has_more": False,
    }


@pytest.mark.asyncio
async def test_list_items_success_with_more_items_to_paginate(
    mock_context,
    mock_httpx_client,
    sample_folder_entry,
    sample_file_entry,
):
    entries = [sample_folder_entry, sample_file_entry]

    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {
        "entries": entries,
        "cursor": "cursor",
        "has_more": True,
    }
    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await list_items_in_folder(
        context=mock_context,
        folder_path="/path/to/folder",
    )

    assert tool_response == {
        "items": clean_dropbox_entries(entries),
        "cursor": "cursor",
        "has_more": True,
    }


@pytest.mark.asyncio
async def test_list_items_success_providing_cursor(
    mock_context,
    mock_httpx_client,
    sample_folder_entry,
    sample_file_entry,
):
    entries = [sample_folder_entry, sample_file_entry]

    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {
        "entries": entries,
        "cursor": "cursor2",
        "has_more": True,
    }
    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await list_items_in_folder(
        context=mock_context,
        folder_path="/path/to/folder",
        cursor="cursor1",
        limit=2,
    )

    assert tool_response == {
        "items": clean_dropbox_entries(entries),
        "cursor": "cursor2",
        "has_more": True,
    }

    # Check that the request was made with the cursor and not the other arguments
    mock_httpx_client.post.assert_called_with(
        url="https://api.dropboxapi.com/2/files/list_folder/continue",
        headers={"Authorization": "Bearer fake-token"},
        json={"cursor": "cursor1"},
    )


@pytest.mark.asyncio
async def test_list_items_path_not_found(
    mock_context,
    mock_httpx_client,
):
    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 409
    mock_httpx_response.json.return_value = {"error_summary": "path/not_found"}

    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await list_items_in_folder(
        context=mock_context,
        folder_path="/not/exist/folder",
    )

    assert tool_response == {
        "error": "The specified path was not found by Dropbox",
    }
