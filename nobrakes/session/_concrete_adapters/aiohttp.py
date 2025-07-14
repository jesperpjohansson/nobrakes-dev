"""
Adapters for `aiohttp` classes.

Provides concrete adapter classes to integrate `aiohttp` with the `nobrakes` framework.
"""

import importlib.util

if importlib.util.find_spec("aiohttp") is None:
    exc_msg = "Missing required dependency 'aiohttp'."
    raise ImportError(exc_msg, __name__, __file__)

from collections.abc import AsyncIterator, MutableMapping
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import override

import aiohttp

from nobrakes.session._base import ResponseAdapter, SessionAdapter

__all__ = ["AIOHTTPResponseAdapter", "AIOHTTPSessionAdapter"]


class AIOHTTPResponseAdapter(ResponseAdapter["aiohttp.ClientResponse"]):
    """Adapter for `aiohttp.ClientResponse`."""

    @override
    def raise_for_status(self) -> None:
        self.adaptee.raise_for_status()

    @override
    def iter_chunks(self, n: int | None = None) -> AsyncIterator[bytes]:
        async def iter_arbitrary_size() -> AsyncIterator[bytes]:
            """Arbitrary chunk size."""
            async for data, _ in self.adaptee.content.iter_chunks():
                yield data

        return self.adaptee.content.iter_chunked(n) if n else iter_arbitrary_size()

    @override
    def iter_lines(self) -> AsyncIterator[bytes]:
        return aiter(self.adaptee.content)

    @override
    async def read(self) -> bytes:
        return await self.adaptee.read()


class AIOHTTPSessionAdapter(
    SessionAdapter[aiohttp.ClientSession, aiohttp.ClientResponse],
):
    """Adapter for `aiohttp.ClientSession`."""

    @override
    def __init__(self, adaptee: aiohttp.ClientSession) -> None:
        adaptee._cookie_jar = aiohttp.DummyCookieJar()  # noqa: SLF001
        super().__init__(adaptee)

    @override
    def request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> AbstractAsyncContextManager[AIOHTTPResponseAdapter]:
        @asynccontextmanager
        async def context_manager() -> AsyncIterator[AIOHTTPResponseAdapter]:
            async with self.adaptee.request(method, url, **kwargs) as response:
                yield AIOHTTPResponseAdapter(response)

        return context_manager()

    @override
    @property
    def headers(self) -> MutableMapping:
        return self.adaptee.headers
