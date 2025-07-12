"""
Adapters for `httpx` classes.

Provides concrete adapter classes to integrate `httpx` with the `nobrakes` framework.
"""

import importlib.util

if importlib.util.find_spec("httpx") is None:
    exc_msg = "Missing required dependency 'httpx'."
    raise ImportError(exc_msg, __name__, __file__)


from collections.abc import AsyncIterator, MutableMapping
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import override

import httpx

from nobrakes.session._base import ResponseAdapter, SessionAdapter
from nobrakes.session._utils import DummyCookieJar

__all__ = ["HTTPXResponseAdapter", "HTTPXSessionAdapter"]


class HTTPXResponseAdapter(ResponseAdapter["httpx.Response"]):
    """Adapter for `httpx.Response`."""

    @override
    def raise_for_status(self) -> "httpx.Response":
        return self.response.raise_for_status()

    @override
    def iter_chunks(self, n: int | None = None) -> AsyncIterator[bytes]:
        return self.response.aiter_bytes(n)

    @override
    def iter_lines(self) -> AsyncIterator[bytes]:
        async def _iter_lines() -> AsyncIterator[bytes]:
            async for line in self.response.aiter_lines():
                yield line.encode("utf-8")

        return _iter_lines()

    @override
    async def read(self) -> bytes:
        return await self.response.aread()


class HTTPXSessionAdapter(SessionAdapter[httpx.AsyncClient, httpx.Response]):
    """Adapter for `httpx.AsyncClient`."""

    @override
    def __init__(self, session: httpx.AsyncClient) -> None:
        session.cookies.jar = DummyCookieJar()
        session.follow_redirects = True
        super().__init__(session)

    @override
    def request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[HTTPXResponseAdapter]:
        @asynccontextmanager
        async def context_manager() -> AsyncIterator[HTTPXResponseAdapter]:
            async with self.session.stream(method, url, **kwargs) as response:
                yield HTTPXResponseAdapter(response)

        return context_manager()

    @override
    @property
    def headers(self) -> MutableMapping:
        return self.session.headers
