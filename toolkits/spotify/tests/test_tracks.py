from unittest.mock import MagicMock

import httpx
import pytest
from arcade.sdk.errors import ToolExecutionError

from arcade_spotify.tools.tracks import (
    get_track_from_id,
)
from arcade_spotify.tools.utils import get_url

SAMPLE_TRACK = {
    "album": {"id": "1234567890", "name": "Test Album", "uri": "spotify:album:1234567890"},
    "artists": [{"name": "Test Artist", "type": "artist", "uri": "spotify:artist:1234567890"}],
    "available_markets": ["us"],
    "duration_ms": 123456,
    "id": "1234567890",
    "is_playable": True,
    "name": "Test Track",
    "popularity": 100,
    "type": "track",
    "uri": "spotify:track:1234567890",
}


@pytest.mark.asyncio
async def test_get_track_from_id_success(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = SAMPLE_TRACK
    mock_httpx_client.request.return_value = mock_response

    result = await get_track_from_id(tool_context, "1234567890")

    assert result == SAMPLE_TRACK

    mock_httpx_client.request.assert_called_once_with(
        "GET",
        get_url("tracks_get_track", track_id="1234567890"),
        headers={"Authorization": f"Bearer {tool_context.authorization.token}"},
        params=None,
        json=None,
    )


@pytest.mark.asyncio
async def test_get_track_from_id_rate_limit_error(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    mock_httpx_client.request.side_effect = mock_response

    with pytest.raises(ToolExecutionError):
        await get_track_from_id(tool_context, "1234567890")
