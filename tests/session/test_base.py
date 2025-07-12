"""Tests for `nobrakes.session.base`."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from nobrakes.session._base import SessionAdapter


@pytest.fixture
def session_adapter():
    class ImplementedSessionAdapter(SessionAdapter):
        @property
        def headers(self):
            pass

        def request(self, method: str, url: str, **kwargs):
            pass

    return ImplementedSessionAdapter(session=Mock())


@pytest.mark.parametrize(
    "method_name", ["get", "post", "put", "delete", "head", "options", "patch"]
)
@pytest.mark.asyncio
async def test_request_is_called_with_args(session_adapter, method_name):
    url = "https://example.com"
    mock_request = MagicMock()
    method = getattr(session_adapter, method_name)

    with patch.object(session_adapter, "request", mock_request):
        async with method(url):
            session_adapter.request.assert_called_with(method_name, url)
