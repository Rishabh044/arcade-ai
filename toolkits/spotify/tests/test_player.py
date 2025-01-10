from unittest.mock import MagicMock, patch

import httpx
import pytest
from arcade.sdk.errors import RetryableToolError, ToolExecutionError

from arcade_spotify.tools.constants import RESPONSE_MSGS
from arcade_spotify.tools.player import (
    adjust_playback_position,
    pause_playback,
    skip_to_next_track,
    skip_to_previous_track,
)
from arcade_spotify.tools.utils import get_url


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_adjust_playback_position_absolute_success(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await adjust_playback_position(context=tool_context, absolute_position_ms=10000)

    assert response == RESPONSE_MSGS["playback_position_adjusted"]

    mock_get_playback_state.assert_not_called()
    mock_httpx_client.request.assert_called_once_with(
        "PUT",
        get_url("player_seek_to_position"),
        headers={"Authorization": f"Bearer {tool_context.authorization.token}"},
        params={"position_ms": 10000},
        json=None,
    )


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_adjust_playback_position_relative_success(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    mock_get_playback_state.return_value = {"device_id": "1234567890", "progress_ms": 10000}
    response = await adjust_playback_position(context=tool_context, relative_position_ms=10000)

    assert response == RESPONSE_MSGS["playback_position_adjusted"]

    mock_get_playback_state.assert_called_once_with(tool_context)
    mock_httpx_client.request.assert_called_once_with(
        "PUT",
        get_url("player_seek_to_position"),
        headers={"Authorization": f"Bearer {tool_context.authorization.token}"},
        params={"position_ms": 20000},
        json=None,
    )


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_adjust_playback_position_both_arguments_error(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    with pytest.raises(RetryableToolError):
        await adjust_playback_position(
            context=tool_context, absolute_position_ms=10000, relative_position_ms=10000
        )

    mock_get_playback_state.assert_not_called()
    mock_httpx_client.assert_not_called()


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_adjust_playback_position_no_arguments_error(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    with pytest.raises(RetryableToolError):
        await adjust_playback_position(context=tool_context)

    mock_get_playback_state.assert_not_called()
    mock_httpx_client.assert_not_called()


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_adjust_playback_position_no_device_error(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_get_playback_state.return_value = {"device_id": None}

    response = await adjust_playback_position(context=tool_context, relative_position_ms=10000)

    assert response == RESPONSE_MSGS["no_track_to_adjust_position"]

    mock_get_playback_state.assert_called_once_with(tool_context)
    mock_httpx_client.assert_not_called()


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_adjust_playback_position_not_found_error(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_httpx_client.request.return_value = mock_response

    response = await adjust_playback_position(context=tool_context, absolute_position_ms=10000)

    assert response == RESPONSE_MSGS["no_track_to_adjust_position"]

    mock_get_playback_state.assert_not_called()
    mock_httpx_client.request.assert_called_once_with(
        "PUT",
        get_url("player_seek_to_position"),
        headers={"Authorization": f"Bearer {tool_context.authorization.token}"},
        params={"position_ms": 10000},
        json=None,
    )


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_adjust_playback_position_too_many_requests_error(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ToolExecutionError):
        await adjust_playback_position(context=tool_context, absolute_position_ms=10000)


@pytest.mark.asyncio
async def test_skip_to_previous_track_success(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await skip_to_previous_track(context=tool_context)

    assert response == RESPONSE_MSGS["playback_skipped_to_previous_track"]


@pytest.mark.asyncio
async def test_skip_to_previous_track_not_found_error(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_httpx_client.request.return_value = mock_response

    response = await skip_to_previous_track(context=tool_context)

    assert response == RESPONSE_MSGS["no_track_to_go_back_to"]


@pytest.mark.asyncio
async def test_skip_to_previous_track_too_many_requests_error(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ToolExecutionError):
        await skip_to_previous_track(context=tool_context)


@pytest.mark.asyncio
async def test_skip_to_next_track_success(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await skip_to_next_track(context=tool_context)

    assert response == RESPONSE_MSGS["playback_skipped_to_next_track"]


@pytest.mark.asyncio
async def test_skip_to_next_track_not_found_error(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_httpx_client.request.return_value = mock_response

    response = await skip_to_next_track(context=tool_context)

    assert response == RESPONSE_MSGS["no_track_to_skip"]


@pytest.mark.asyncio
async def test_skip_to_next_track_too_many_requests_error(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ToolExecutionError):
        await skip_to_next_track(context=tool_context)


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_pause_playback_success(mock_get_playback_state, tool_context, mock_httpx_client):
    mock_get_playback_state.return_value = {"device_id": "1234567890", "is_playing": True}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await pause_playback(context=tool_context)
    assert response == RESPONSE_MSGS["playback_paused"]


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_pause_playback_no_device_running(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_get_playback_state.return_value = {"device_id": None}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await pause_playback(context=tool_context)
    assert response == RESPONSE_MSGS["no_track_to_pause"]
    mock_httpx_client.assert_not_called()


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_pause_playback_already_paused_success(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_get_playback_state.return_value = {"device_id": "1234567890", "is_playing": False}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await pause_playback(context=tool_context)
    assert response == RESPONSE_MSGS["track_is_already_paused"]
    mock_httpx_client.assert_not_called()


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_pause_playback_too_many_requests_error(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_get_playback_state.return_value = {"device_id": "1234567890", "is_playing": True}

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ToolExecutionError):
        await pause_playback(context=tool_context)


@pytest.mark.asyncio
async def test_resume_playback_success(tool_context, mock_httpx_client):
    pass


@pytest.mark.asyncio
async def test_start_tracks_playback_by_id_success(tool_context, mock_httpx_client):
    pass


@pytest.mark.asyncio
async def test_get_playback_state_success(tool_context, mock_httpx_client):
    pass


@pytest.mark.asyncio
async def test_get_currently_playing_success(tool_context, mock_httpx_client):
    pass


@pytest.mark.asyncio
async def test_play_artist_by_name_success(tool_context, mock_httpx_client):
    pass


@pytest.mark.asyncio
async def test_play_track_by_name_success(tool_context, mock_httpx_client):
    pass


@pytest.mark.asyncio
async def test_get_available_devices_success(tool_context, mock_httpx_client):
    pass
