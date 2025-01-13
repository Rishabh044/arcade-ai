from unittest.mock import MagicMock, patch

import httpx
import pytest
from arcade.sdk.errors import RetryableToolError, ToolExecutionError

from arcade_spotify.tools.constants import RESPONSE_MSGS
from arcade_spotify.tools.models import SearchType
from arcade_spotify.tools.player import (
    adjust_playback_position,
    get_available_devices,
    get_currently_playing,
    get_playback_state,
    pause_playback,
    play_artist_by_name,
    play_track_by_name,
    resume_playback,
    skip_to_next_track,
    skip_to_previous_track,
    start_tracks_playback_by_id,
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
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_resume_playback_success(mock_get_playback_state, tool_context, mock_httpx_client):
    mock_get_playback_state.return_value = {"device_id": "1234567890", "is_playing": False}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await resume_playback(context=tool_context)
    assert response == RESPONSE_MSGS["playback_resumed"]


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_resume_playback_no_device_running(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_get_playback_state.return_value = {"device_id": None}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await resume_playback(context=tool_context)
    assert response == RESPONSE_MSGS["no_track_to_resume"]
    mock_httpx_client.assert_not_called()


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_resume_playback_already_playing_success(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_get_playback_state.return_value = {"device_id": "1234567890", "is_playing": True}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await resume_playback(context=tool_context)
    assert response == RESPONSE_MSGS["track_is_already_playing"]
    mock_httpx_client.assert_not_called()


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_playback_state")
async def test_resume_playback_too_many_requests_error(
    mock_get_playback_state, tool_context, mock_httpx_client
):
    mock_get_playback_state.return_value = {"device_id": "1234567890", "is_playing": False}

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ToolExecutionError):
        await resume_playback(context=tool_context)


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_available_devices")
async def test_start_tracks_playback_by_id_success(
    mock_get_available_devices, tool_context, mock_httpx_client
):
    mock_get_available_devices.return_value = {
        "devices": [
            {
                "id": "1234567890",
                "is_active": True,
                "name": "Test Device",
                "type": "Computer",
                "is_private_session": False,
                "is_restricted": False,
                "supports_volume": True,
                "volume_percent": 100,
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await start_tracks_playback_by_id(
        context=tool_context, track_ids=["1234567890"], position_ms=10000
    )
    assert response == RESPONSE_MSGS["playback_started"]


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_available_devices")
async def test_start_tracks_playback_by_id_no_active_device(
    mock_get_available_devices, tool_context, mock_httpx_client
):
    mock_get_available_devices.return_value = {"devices": []}
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_httpx_client.request.return_value = mock_response

    response = await start_tracks_playback_by_id(
        context=tool_context, track_ids=["1234567890"], position_ms=10000
    )
    assert response == RESPONSE_MSGS["no_active_device"]


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.get_available_devices")
async def test_start_tracks_playback_by_id_too_many_requests_error(
    mock_get_available_devices, tool_context, mock_httpx_client
):
    mock_get_available_devices.return_value = {
        "devices": [
            {
                "id": "1234567890",
                "is_active": True,
                "name": "Test Device",
                "type": "Computer",
                "is_private_session": False,
                "is_restricted": False,
                "supports_volume": True,
                "volume_percent": 100,
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ToolExecutionError):
        await start_tracks_playback_by_id(
            context=tool_context, track_ids=["1234567890"], position_ms=10000
        )


@pytest.mark.asyncio
async def test_get_playback_state_success(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "device": {
            "id": "1234567890",
            "is_active": True,
            "name": "Test Device",
            "type": "Computer",
        },
        "currently_playing_type": "track",
        "is_playing": True,
        "progress_ms": 10000,
        "message": "Playback started",
    }
    mock_httpx_client.request.return_value = mock_response

    response = await get_playback_state(context=tool_context)

    assert response["device_id"] == "1234567890"
    assert response["device_name"] == "Test Device"
    assert response["is_playing"] is True
    assert response["progress_ms"] == 10000
    assert response["message"] == "Playback started"


@pytest.mark.asyncio
async def test_get_playback_state_playback_not_active(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_httpx_client.request.return_value = mock_response

    response = await get_playback_state(context=tool_context)

    assert response["is_playing"] is False


@pytest.mark.asyncio
async def test_get_playback_state_too_many_requests_error(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ToolExecutionError):
        await get_playback_state(context=tool_context)


@pytest.mark.asyncio
async def test_get_currently_playing_success(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "device": {
            "id": "1234567890",
            "is_active": True,
            "name": "Test Device",
            "type": "Computer",
        },
        "currently_playing_type": "track",
        "is_playing": True,
        "progress_ms": 10000,
        "message": "Playback started",
    }
    mock_httpx_client.request.return_value = mock_response

    response = await get_currently_playing(context=tool_context)

    assert response["device_id"] == "1234567890"
    assert response["device_name"] == "Test Device"
    assert response["is_playing"] is True
    assert response["progress_ms"] == 10000
    assert response["message"] == "Playback started"


@pytest.mark.asyncio
async def test_get_currently_playing_playback_not_active(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_httpx_client.request.return_value = mock_response

    response = await get_currently_playing(context=tool_context)

    assert response["is_playing"] is False


@pytest.mark.asyncio
async def test_get_currently_playing_too_many_requests_error(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ToolExecutionError):
        await get_currently_playing(context=tool_context)


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.start_tracks_playback_by_id")
@patch("arcade_spotify.tools.player.search")
async def test_play_artist_by_name_success(
    mock_search, mock_start_tracks_playback_by_id, tool_context, mock_httpx_client
):
    track_id = "1234567890"
    mock_search.return_value = {"tracks": {"items": [{"id": track_id, "name": "Test Track"}]}}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    mock_start_tracks_playback_by_id.return_value = RESPONSE_MSGS["playback_started"]

    response = await play_artist_by_name(context=tool_context, name="Test Artist")

    assert response == RESPONSE_MSGS["playback_started"]

    mock_search.assert_called_once_with(tool_context, "artist:Test Artist", [SearchType.TRACK], 5)
    mock_start_tracks_playback_by_id.assert_called_once_with(tool_context, [track_id])


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.start_tracks_playback_by_id")
@patch("arcade_spotify.tools.player.search")
async def test_play_artist_by_name_no_tracks_found(
    mock_search, mock_start_tracks_playback_by_id, tool_context, mock_httpx_client
):
    mock_search.return_value = {"tracks": {"items": []}}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    mock_start_tracks_playback_by_id.return_value = RESPONSE_MSGS["playback_started"]

    artist_name = "Test Artist"

    with pytest.raises(RetryableToolError) as e:
        await play_artist_by_name(context=tool_context, name=artist_name)
        assert e.value.message == RESPONSE_MSGS["artist_not_found"].format(artist_name=artist_name)

    mock_search.assert_called_once_with(tool_context, "artist:Test Artist", [SearchType.TRACK], 5)
    mock_start_tracks_playback_by_id.assert_not_called()


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.start_tracks_playback_by_id")
@patch("arcade_spotify.tools.player.search")
async def test_play_track_by_name_success(
    mock_search, mock_start_tracks_playback_by_id, tool_context, mock_httpx_client
):
    track_id = "1234567890"
    mock_search.return_value = {"tracks": {"items": [{"id": track_id, "name": "Test Track"}]}}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await play_track_by_name(context=tool_context, track_name="Test Track")

    assert response == str(mock_start_tracks_playback_by_id.return_value)

    mock_search.assert_called_once_with(tool_context, "track:Test Track", [SearchType.TRACK], 1)
    mock_start_tracks_playback_by_id.assert_called_once_with(tool_context, [track_id])


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.start_tracks_playback_by_id")
@patch("arcade_spotify.tools.player.search")
async def test_play_track_by_name_with_artist_success(
    mock_search, mock_start_tracks_playback_by_id, tool_context, mock_httpx_client
):
    track_id = "1234567890"
    mock_search.return_value = {"tracks": {"items": [{"id": track_id, "name": "Test Track"}]}}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    response = await play_track_by_name(
        context=tool_context, track_name="Test Track", artist_name="Test Artist"
    )

    assert response == str(mock_start_tracks_playback_by_id.return_value)

    mock_search.assert_called_once_with(
        tool_context, "track:Test Track artist:Test Artist", [SearchType.TRACK], 1
    )
    mock_start_tracks_playback_by_id.assert_called_once_with(tool_context, [track_id])


@pytest.mark.asyncio
@patch("arcade_spotify.tools.player.start_tracks_playback_by_id")
@patch("arcade_spotify.tools.player.search")
async def test_play_track_by_name_no_tracks_found(
    mock_search, mock_start_tracks_playback_by_id, tool_context, mock_httpx_client
):
    mock_search.return_value = {"tracks": {"items": []}}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(RetryableToolError) as e:
        await play_track_by_name(context=tool_context, track_name="Test Track")
        assert e.value.message == RESPONSE_MSGS["track_not_found"].format(track_name="Test Track")

    mock_search.assert_called_once_with(tool_context, "track:Test Track", [SearchType.TRACK], 1)
    mock_start_tracks_playback_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_get_available_devices_success(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "devices": [{"id": "1234567890", "name": "Test Device", "type": "Computer"}]
    }
    mock_httpx_client.request.return_value = mock_response

    response = await get_available_devices(context=tool_context)
    assert response == dict(mock_response.json())


@pytest.mark.asyncio
async def test_get_available_devices_too_many_requests(tool_context, mock_httpx_client):
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Too Many Requests", request=MagicMock(), response=MagicMock(status_code=429)
    )
    mock_httpx_client.request.return_value = mock_response

    with pytest.raises(ToolExecutionError):
        await get_available_devices(context=tool_context)
