import httpx
import pytest
import respx
from arcade.sdk.errors import RetryableToolError

from arcade_dropbox.tools.base import (
    download_file,
    list_folder_contents,
    search_files,
    update_file_contents,
)


@respx.mock
def test_search_files(tool_context):
    url = "https://api.dropboxapi.com/2/files/search_v2"
    expected_metadata = {"name": "test.txt", "path_lower": "/test.txt"}
    mock_response = {"matches": [{"metadata": {"metadata": expected_metadata}}]}
    respx.post(
        url,
        json__eq={
            "query": "test",
            "options": {
                "path": "/",
                "max_results": 100,
                "filename_only": True,
                "file_status": "active",
            },
        },
    ).mock(return_value=httpx.Response(200, json=mock_response))

    results = search_files(tool_context, "test")
    assert results == [expected_metadata]


@respx.mock
def test_list_folder_contents(tool_context):
    list_url = "https://api.dropboxapi.com/2/files/list_folder"
    continue_url = "https://api.dropboxapi.com/2/files/list_folder/continue"

    initial_response = {
        "entries": [{"name": "file1.txt", ".tag": "file"}],
        "has_more": True,
        "cursor": "dummy_cursor",
    }
    continue_response = {"entries": [{"name": "file2.txt", ".tag": "file"}], "has_more": False}
    respx.post(list_url, json__eq={"path": "/folder", "recursive": True}).mock(
        return_value=httpx.Response(200, json=initial_response)
    )
    respx.post(continue_url, json__eq={"cursor": "dummy_cursor"}).mock(
        return_value=httpx.Response(200, json=continue_response)
    )

    results = list_folder_contents(tool_context, "/folder")
    assert len(results) == 2
    names = [entry.get("name") for entry in results]
    assert "file1.txt" in names
    assert "file2.txt" in names


@respx.mock
def test_list_folder_contents_filter(tool_context):
    list_url = "https://api.dropboxapi.com/2/files/list_folder"
    response_data = {
        "entries": [
            {"name": "file1.txt", ".tag": "file"},
            {"name": "file2.jpg", ".tag": "file"},
            {"name": "folder", ".tag": "folder"},
        ],
        "has_more": False,
    }
    respx.post(list_url).mock(return_value=httpx.Response(200, json=response_data))

    results = list_folder_contents(tool_context, "/folder", filetype=".txt")
    assert len(results) == 1
    assert results[0]["name"] == "file1.txt"


@respx.mock
def test_download_file(tool_context):
    url = "https://content.dropboxapi.com/2/files/download"
    file_content = "This is the file content."
    respx.post(url).mock(return_value=httpx.Response(200, text=file_content))

    result = download_file(tool_context, "/dummy/path")
    assert result == file_content


@respx.mock
def test_update_file_contents(tool_context):
    url = "https://content.dropboxapi.com/2/files/upload"
    response_json = {"name": "updated_file.txt"}
    respx.post(url).mock(return_value=httpx.Response(200, json=response_json))

    result = update_file_contents(tool_context, "/dummy/path", "new content")
    assert result == "File 'updated_file.txt' updated successfully."


@respx.mock
def test_search_files_error(tool_context):
    url = "https://api.dropboxapi.com/2/files/search_v2"
    respx.post(url).mock(return_value=httpx.Response(400, text="Bad Request"))

    with pytest.raises(RetryableToolError):
        search_files(tool_context, "error")
