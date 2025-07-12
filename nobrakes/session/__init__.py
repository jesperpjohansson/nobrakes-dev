"""Package docstring."""

from nobrakes.session._base import ResponseAdapter, SessionAdapter
from nobrakes.session._concrete_adapters import (
    AIOHTTPResponseAdapter,
    AIOHTTPSessionAdapter,
    HTTPXResponseAdapter,
    HTTPXSessionAdapter,
)
from nobrakes.session._utils import DummyCookieJar

__all__ = [
    "AIOHTTPResponseAdapter",
    "AIOHTTPSessionAdapter",
    "DummyCookieJar",
    "HTTPXResponseAdapter",
    "HTTPXSessionAdapter",
    "ResponseAdapter",
    "SessionAdapter",
]
