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

from nobrakes.client._base import ResponseAdapter, SessionAdapter
from nobrakes.client._utils import DummyCookieJar

__all__ = ["HTTPXResponseAdapter", "HTTPXSessionAdapter"]


class HTTPXResponseAdapter(ResponseAdapter["httpx.Response"]):
    """Adapter for `httpx.Response`."""

    @override
    def raise_for_status(self) -> "httpx.Response":
        return self.adaptee.raise_for_status()

    @override
    def iter_chunks(self) -> AsyncIterator[bytes]:
        return self.adaptee.aiter_bytes()

    @override
    def iter_lines(self) -> AsyncIterator[bytes]:
        async def _iter_lines() -> AsyncIterator[bytes]:
            async for line in self.adaptee.aiter_lines():
                yield line.encode("utf-8")

        return _iter_lines()

    @override
    async def read(self) -> bytes:
        return await self.adaptee.aread()


class HTTPXSessionAdapter(SessionAdapter[httpx.AsyncClient, httpx.Response]):
    """Adapter for `httpx.AsyncClient`."""

    @override
    def __init__(self, adaptee: httpx.AsyncClient) -> None:
        adaptee.cookies.jar = DummyCookieJar()
        adaptee.follow_redirects = True
        super().__init__(adaptee)

    @override
    def request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[HTTPXResponseAdapter]:
        @asynccontextmanager
        async def context_manager() -> AsyncIterator[HTTPXResponseAdapter]:
            async with self.adaptee.stream(method, url, **kwargs) as response:
                yield HTTPXResponseAdapter(response)

        return context_manager()

    @override
    @property
    def headers(self) -> MutableMapping:
        return self.adaptee.headers
