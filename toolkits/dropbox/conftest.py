import pytest


class DummyAuth:
    token: str = "dummy_access_token"


class DummyToolContext:
    authorization = DummyAuth()

    def get_auth_token_or_empty(self) -> str:
        return self.authorization.token


@pytest.fixture
def tool_context():
    return DummyToolContext()
