"""Package docstring."""

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
