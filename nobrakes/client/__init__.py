"""
Tools for adapting third-party asynchronous HTTP libraries.

This subpackage provides base classes, concrete implementations, and utilities for
adapting asynchronous HTTP libraries to a common interface used by the `nobrakes`
framework.

Classes
-------
ResponseAdapter
    Abstract base class for HTTP response adapters.
SessionAdapter
    Abstract base class for asynchronous HTTP client session adapters.
AIOHTTPResponseAdapter
    Adapter for `aiohttp.ClientResponse`.
AIOHTTPSessionAdapter
    Adapter for `aiohttp.ClientSession`.
HTTPXResponseAdapter
    Adapter for `httpx.Response`.
HTTPXSessionAdapter
    Adapter for `httpx.AsyncClient`.
DummyCookieJar
    Subclass of `http.cookiejar.CookieJar` that inhibits cookie extraction from
    HTTP responses.
"""

from nobrakes.client._base import ResponseAdapter, SessionAdapter
from nobrakes.client._support import (
    AIOHTTPResponseAdapter,
    AIOHTTPSessionAdapter,
    HTTPXResponseAdapter,
    HTTPXSessionAdapter,
)
from nobrakes.client._utils import DummyCookieJar

__all__ = [
    "AIOHTTPResponseAdapter",
    "AIOHTTPSessionAdapter",
    "DummyCookieJar",
    "HTTPXResponseAdapter",
    "HTTPXSessionAdapter",
    "ResponseAdapter",
    "SessionAdapter",
]
