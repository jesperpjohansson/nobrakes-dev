"""
Concrete implementations of the abstract adapters in `nobrakes/session/_base.py`.

This module conditionally imports adapter classes for supported HTTP libraries
(e.g., aiohttp, httpx). If a required library is not installed, an
ImportError is raised when the missing class is accessed.
"""

from collections.abc import Callable
from importlib.util import find_spec
from typing import TYPE_CHECKING, NoReturn


def _missing(dep: str, cls: str) -> Callable:
    def _raise(*_: object, **__: object) -> NoReturn:
        exc_msg = (
            f"'{cls}' requires dependency '{dep}'. "
            f"Install with `pip install nobrakes[{dep}]`."
        )
        raise ImportError(exc_msg)

    return _raise


if TYPE_CHECKING:
    from nobrakes.session._concrete_adapters.aiohttp import (
        AIOHTTPResponseAdapter,
        AIOHTTPSessionAdapter,
    )
    from nobrakes.session._concrete_adapters.httpx import (
        HTTPXResponseAdapter,
        HTTPXSessionAdapter,
    )
else:
    if find_spec("aiohttp") is not None:
        from nobrakes.session._concrete_adapters.aiohttp import (
            AIOHTTPResponseAdapter,
            AIOHTTPSessionAdapter,
        )
    else:
        AIOHTTPResponseAdapter = _missing("aiohttp", "AIOHTTPResponseAdapter")
        AIOHTTPSessionAdapter = _missing("aiohttp", "AIOHTTPSessionAdapter")

    if find_spec("httpx") is not None:
        from nobrakes.session._concrete_adapters.httpx import (
            HTTPXResponseAdapter,
            HTTPXSessionAdapter,
        )
    else:
        HTTPXResponseAdapter = _missing("httpx", "HTTPXResponseAdapter")
        HTTPXSessionAdapter = _missing("httpx", "HTTPXSessionAdapter")

__all__ = [
    "AIOHTTPResponseAdapter",
    "AIOHTTPSessionAdapter",
    "HTTPXResponseAdapter",
    "HTTPXSessionAdapter",
]
