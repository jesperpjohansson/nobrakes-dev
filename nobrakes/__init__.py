"""..."""

from collections.abc import Callable
from importlib.util import find_spec
from typing import TYPE_CHECKING, NoReturn

from nobrakes import pgelements, pgmodel, typing
from nobrakes._scraper import SVEMOScraper
from nobrakes._session.base import ResponseAdapter, SessionAdapter
from nobrakes._session.utils import DummyCookieJar


def _missing(dep: str, cls: str) -> Callable:
    def _raise(*_: object, **__: object) -> NoReturn:
        exc_msg = (
            f"'{cls}' requires dependency '{dep}'. "
            f"Install with `pip install nobrakes[{dep}]`."
        )
        raise ImportError(exc_msg)

    return _raise


if TYPE_CHECKING:
    from nobrakes._session.adapters.aiohttp import (
        AIOHTTPResponseAdapter,
        AIOHTTPSessionAdapter,
    )
    from nobrakes._session.adapters.httpx import (
        HTTPXResponseAdapter,
        HTTPXSessionAdapter,
    )
else:
    if find_spec("aiohttp") is not None:
        from nobrakes._session.adapters.aiohttp import (
            AIOHTTPResponseAdapter,
            AIOHTTPSessionAdapter,
        )
    else:
        AIOHTTPResponseAdapter = _missing("aiohttp", "AIOHTTPResponseAdapter")
        AIOHTTPSessionAdapter = _missing("aiohttp", "AIOHTTPSessionAdapter")

    if find_spec("httpx") is not None:
        from nobrakes._session.adapters.httpx import (
            HTTPXResponseAdapter,
            HTTPXSessionAdapter,
        )
    else:
        HTTPXResponseAdapter = _missing("httpx", "HTTPXResponseAdapter")
        HTTPXSessionAdapter = _missing("httpx", "HTTPXSessionAdapter")


__all__ = [
    "AIOHTTPResponseAdapter",
    "AIOHTTPSessionAdapter",
    "DummyCookieJar",
    "HTTPXResponseAdapter",
    "HTTPXSessionAdapter",
    "ResponseAdapter",
    "SVEMOScraper",
    "SessionAdapter",
    "pgelements",
    "pgmodel",
    "typing",
]
