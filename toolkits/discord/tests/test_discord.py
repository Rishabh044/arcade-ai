import pytest
from arcade.sdk.errors import ToolExecutionError
from toolkits.discord.arcade_discord.tools.user import get_current_user


def test_hello() -> None:
    assert get_current_user("developer") == "Hello, developer!"


def test_hello_raises_error() -> None:
    with pytest.raises(ToolExecutionError):
        get_current_user(1)
