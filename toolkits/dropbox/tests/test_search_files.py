from unittest.mock import MagicMock

import httpx
import pytest

from arcade_dropbox.constants import ItemCategory
from arcade_dropbox.tools.browse import search_files_and_folders
from arcade_dropbox.utils import clean_dropbox_entry


@pytest.fixture
def sample_folder_match(sample_folder_entry):
    return {
        "metadata": {
            ".tag": "metadata",
            "metadata": sample_folder_entry,
        }
    }


@pytest.fixture
def sample_file_match(sample_file_entry):
    return {
        "metadata": {
            ".tag": "metadata",
            "metadata": sample_file_entry,
        }
    }


@pytest.mark.asyncio
async def test_search_files_success_empty_results(
    mock_context,
    mock_httpx_client,
):
    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {"matches": [], "cursor": None, "has_more": False}
    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await search_files_and_folders(
        context=mock_context,
        keywords="do not match anything",
    )

    assert tool_response == {
        "items": [],
        "cursor": None,
        "has_more": False,
    }


@pytest.mark.asyncio
async def test_search_files_success_with_matches(
    mock_context,
    mock_httpx_client,
    sample_file_match,
    sample_folder_match,
    sample_file_entry,
    sample_folder_entry,
):
    matches = [
        sample_file_match,
        sample_folder_match,
    ]

    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {"matches": matches, "cursor": None, "has_more": False}
    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await search_files_and_folders(
        context=mock_context,
        keywords="test",
    )

    assert tool_response == {
        "items": [
            clean_dropbox_entry(sample_file_entry),
            clean_dropbox_entry(sample_folder_entry),
        ],
        "cursor": None,
        "has_more": False,
    }


@pytest.mark.asyncio
async def test_search_files_success_with_path_missing_leading_slash(
    mock_context,
    mock_httpx_client,
    sample_file_match,
    sample_folder_match,
    sample_file_entry,
    sample_folder_entry,
):
    matches = [
        sample_file_match,
        sample_folder_match,
    ]

    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {"matches": matches, "cursor": None, "has_more": False}
    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await search_files_and_folders(
        context=mock_context,
        keywords="test",
        search_in_folder_path="TestFolder",
    )

    assert tool_response == {
        "items": [
            clean_dropbox_entry(sample_file_entry),
            clean_dropbox_entry(sample_folder_entry),
        ],
        "cursor": None,
        "has_more": False,
    }

    mock_httpx_client.post.assert_called_once_with(
        url="https://api.dropboxapi.com/2/files/search_v2",
        headers={"Authorization": "Bearer fake-token"},
        json={
            "query": "test",
            "options": {
                "file_categories": [],
                "path": "/TestFolder",
                "file_status": "active",
                "filename_only": False,
                "max_results": 100,
            },
        },
    )


@pytest.mark.asyncio
async def test_search_files_success_with_more_results_to_paginate(
    mock_context,
    mock_httpx_client,
    sample_file_match,
    sample_folder_match,
    sample_file_entry,
    sample_folder_entry,
):
    matches = [
        sample_file_match,
        sample_folder_match,
    ]

    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {
        "matches": matches,
        "cursor": "cursor",
        "has_more": True,
    }
    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await search_files_and_folders(
        context=mock_context,
        keywords="test",
    )

    assert tool_response == {
        "items": [
            clean_dropbox_entry(sample_file_entry),
            clean_dropbox_entry(sample_folder_entry),
        ],
        "cursor": "cursor",
        "has_more": True,
    }


@pytest.mark.asyncio
async def test_search_files_success_providing_pagination_cursor(
    mock_context,
    mock_httpx_client,
    sample_file_match,
    sample_folder_match,
    sample_file_entry,
    sample_folder_entry,
):
    matches = [
        sample_file_match,
        sample_folder_match,
    ]

    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {"matches": matches, "cursor": None, "has_more": False}
    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await search_files_and_folders(
        context=mock_context,
        keywords="test",
        cursor="cursor",
    )

    assert tool_response == {
        "items": [
            clean_dropbox_entry(sample_file_entry),
            clean_dropbox_entry(sample_folder_entry),
        ],
        "cursor": None,
        "has_more": False,
    }

    # Assert that the request was made with the correct cursor and not other arguments
    mock_httpx_client.post.assert_called_once_with(
        url="https://api.dropboxapi.com/2/files/search_v2/continue",
        headers={"Authorization": "Bearer fake-token"},
        json={"cursor": "cursor"},
    )


@pytest.mark.asyncio
async def test_search_files_path_not_found(
    mock_context,
    mock_httpx_client,
):
    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 409
    mock_httpx_response.json.return_value = {"error_summary": "path/not_found"}

    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await search_files_and_folders(
        context=mock_context,
        keywords="test",
        search_in_folder_path="/not/exist/folder",
    )

    assert tool_response == {
        "error": "The specified path was not found by Dropbox",
    }


@pytest.mark.asyncio
async def test_search_files_success_filtering_by_category(
    mock_context,
    mock_httpx_client,
    sample_file_match,
    sample_folder_match,
    sample_file_entry,
    sample_folder_entry,
):
    matches = [
        sample_file_match,
        sample_folder_match,
    ]

    mock_httpx_response = MagicMock(spec=httpx.Response)
    mock_httpx_response.status_code = 200
    mock_httpx_response.json.return_value = {"matches": matches, "cursor": None, "has_more": False}
    mock_httpx_client.post.return_value = mock_httpx_response

    tool_response = await search_files_and_folders(
        context=mock_context,
        keywords="test",
        filter_by_category=[ItemCategory.PDF],
    )

    assert tool_response == {
        "items": [
            clean_dropbox_entry(sample_file_entry),
            clean_dropbox_entry(sample_folder_entry),
        ],
        "cursor": None,
        "has_more": False,
    }

    mock_httpx_client.post.assert_called_once_with(
        url="https://api.dropboxapi.com/2/files/search_v2",
        headers={"Authorization": "Bearer fake-token"},
        json={
            "query": "test",
            "options": {
                "path": "",
                "file_status": "active",
                "filename_only": False,
                "max_results": 100,
                "file_categories": [ItemCategory.PDF.value],
            },
        },
    )
