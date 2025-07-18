"""Tests for `nobrakes.session._concrete_adapters`."""

import importlib
import sys
from unittest.mock import AsyncMock, MagicMock, Mock

import aiohttp
import pytest

from nobrakes.session._concrete_adapters import aiohttp as a_aiohttp, httpx as a_httpx
from nobrakes.session._utils import DummyCookieJar


@pytest.mark.parametrize(
    ("lib", "class_name"),
    [
        ("aiohttp", "AIOHTTPResponseAdapter"),
        ("aiohttp", "AIOHTTPSessionAdapter"),
        ("httpx", "HTTPXResponseAdapter"),
        ("httpx", "HTTPXSessionAdapter"),
    ],
)
def test_adapter_raises_if_missing_dependency(monkeypatch, lib, class_name):
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda name: None if name == lib else "not_none"
    )

    sys.modules.pop("nobrakes.session._concrete_adapters", None)
    module = importlib.import_module("nobrakes.session._concrete_adapters")
    missing_class = getattr(module, class_name)
    with pytest.raises(ImportError, match=f"{class_name}.*{lib}"):
        missing_class()


@pytest.mark.parametrize("lib", ["aiohttp", "httpx"])
def test_module_raises_if_missing_dependency(lib, monkeypatch):
    module_path = f"nobrakes.session._concrete_adapters.{lib}"

    # Ensure a fresh import
    sys.modules.pop(module_path, None)
    monkeypatch.setattr(importlib.util, "find_spec", lambda _: None)

    # Patch the correct path to find_spec inside the target module
    with pytest.raises(ImportError, match=f"Missing required dependency '{lib}'"):
        importlib.import_module(module_path)


class TestSessionAdapters:
    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.mark.parametrize(
        ("module", "request_method_name", "s_adapter_name", "r_adapter_name"),
        [
            (a_aiohttp, "request", "AIOHTTPSessionAdapter", "AIOHTTPResponseAdapter"),
            (a_httpx, "stream", "HTTPXSessionAdapter", "HTTPXResponseAdapter"),
        ],
    )
    @pytest.mark.asyncio
    async def test_request_method_wraps_response(
        self, mock_session, module, request_method_name, s_adapter_name, r_adapter_name
    ):
        request_method = getattr(mock_session, request_method_name)

        adapter_type = getattr(module, r_adapter_name)
        session_adapter_type = getattr(module, s_adapter_name)

        session_adapter = session_adapter_type(mock_session)

        async with session_adapter.request("get", "http://example.com") as response:
            assert isinstance(response, adapter_type)

        request_method.assert_called_once_with("get", "http://example.com")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "adapter_type", [a_aiohttp.AIOHTTPSessionAdapter, a_httpx.HTTPXSessionAdapter]
    )
    async def test_session_adapter_headers_returns_session_headers(
        self, mock_session, adapter_type
    ):
        headers = {"User-Agent": "test-agent"}
        mock_session.headers = headers
        adapter = adapter_type(mock_session)
        assert adapter.headers == headers

    @pytest.mark.asyncio
    async def test_aiohttp_session_adapter_sets_dummy_cookie_jar(self, mock_session):
        _ = a_aiohttp.AIOHTTPSessionAdapter(mock_session)
        assert type(mock_session._cookie_jar) is aiohttp.DummyCookieJar

    def test_httpx_session_adapter_sets_dummy_cookie_jar(self, mock_session):
        _ = a_httpx.HTTPXSessionAdapter(mock_session)
        assert type(mock_session.cookies.jar) is DummyCookieJar

    def test_httpx_session_adapter_enables_redirects(self, mock_session):
        _ = a_httpx.HTTPXSessionAdapter(mock_session)
        assert mock_session.follow_redirects is True


@pytest.mark.asyncio
class TestResponseAdapters:
    @pytest.fixture(scope="class")
    def markup(self):
        return b"""
        <!DOCTYPE html>
        <html lang="en">
            <head></head>
            <body></body>
        </html>
        """

    @pytest.mark.parametrize(
        "adapter_type",
        [a_aiohttp.AIOHTTPResponseAdapter, a_httpx.HTTPXResponseAdapter],
    )
    async def test_calls_session_raise_for_status(self, adapter_type):
        mock_response = MagicMock()
        response_adapter = adapter_type(adaptee=mock_response)
        response_adapter.raise_for_status()
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.parametrize(
        ("adapter_type", "read_method_name"),
        [
            (a_aiohttp.AIOHTTPResponseAdapter, "read"),
            (a_httpx.HTTPXResponseAdapter, "aread"),
        ],
    )
    async def test_read_returns_data(self, markup, adapter_type, read_method_name):
        mock_response = Mock()
        setattr(mock_response, read_method_name, AsyncMock(return_value=markup))
        response_adapter = adapter_type(mock_response)
        assert await response_adapter.read() == markup

    @pytest.mark.parametrize(
        ("adapter_type", "method_name"),
        [
            (a_aiohttp.AIOHTTPResponseAdapter, "iter_chunks"),
            (a_httpx.HTTPXResponseAdapter, "aiter_bytes"),
        ],
    )
    async def test_iter_chunks_returns_chunks_iterator(
        self, markup, adapter_type, method_name
    ):
        def chunk_iterator(n=None):
            async def _iter():
                if n is None:
                    yield (markup, None) if method_name == "iter_chunks" else markup
                else:
                    for i in range(0, len(markup), n):
                        yield markup[i : i + n]

            return _iter()

        mock_response = MagicMock()

        if method_name == "iter_chunks":
            # aiohttp adapter
            mock_response.content = Mock()
            mock_response.content.iter_chunks = chunk_iterator
            mock_response.content.iter_chunked = chunk_iterator
        else:
            # httpx adapter
            mock_response.aiter_bytes = chunk_iterator

        adapter = adapter_type(mock_response)

        chunks = [chunk async for chunk in adapter.iter_chunks()]
        assert chunks == [markup]

        chunks = [chunk async for chunk in adapter.iter_chunks(n=30)]
        expected = [markup[i : i + 30] for i in range(0, len(markup), 30)]
        assert chunks == expected

    @pytest.mark.parametrize(
        "adapter_type",
        [a_aiohttp.AIOHTTPResponseAdapter, a_httpx.HTTPXResponseAdapter],
    )
    async def test_iter_lines_yields_lines(self, markup, adapter_type):
        mock_response = MagicMock()
        expected_lines = markup.splitlines()

        def iter_lines(*_):
            async def _str():
                for line in expected_lines:
                    yield line.decode()

            async def _bytes():
                for line in expected_lines:
                    yield line

            name = adapter_type.__name__
            return _str() if name == "HTTPXResponseAdapter" else _bytes()

        if adapter_type.__name__ == "AIOHTTPResponseAdapter":
            mock_response.content = MagicMock()
            mock_response.content.__aiter__ = iter_lines
        else:
            mock_response.aiter_lines = iter_lines

        adapter = adapter_type(mock_response)

        lines = [line async for line in adapter.iter_lines()]
        assert lines == markup.splitlines()
