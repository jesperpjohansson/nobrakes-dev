"""Tests for `nobrakes.session.base`."""

from unittest.mock import MagicMock, patch

import pytest

from nobrakes.session._base import SessionAdapter


@pytest.fixture
def dummy_session_adapter():
    class ImplementedSessionAdapter(SessionAdapter):
        @property
        def headers(self):
            pass

        def request(self, *_, **__):
            pass

    return ImplementedSessionAdapter(adaptee=None)


@pytest.mark.parametrize(
    "method_name", ["get", "post", "put", "delete", "head", "options", "patch"]
)
@pytest.mark.asyncio
async def test_request_is_called_with_args(dummy_session_adapter, method_name):
    url = "https://example.com"
    method = getattr(dummy_session_adapter, method_name)

    with patch.object(dummy_session_adapter, "request", MagicMock()):
        async with method(url):
            dummy_session_adapter.request.assert_called_with(method_name, url)
