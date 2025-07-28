"""Various useful utilities for asynchronous HTTP client sessions."""

from __future__ import annotations

import asyncio
import http.cookiejar
import random
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from collections.abc import Awaitable


class DummyCookieJar(http.cookiejar.CookieJar):
    """A cookie jar that inhibits cookie extraction from HTTP responses."""

    @override
    def extract_cookies(self, *_: object) -> None:
        pass


async def with_delay[R](t: float, coro: Awaitable[R]) -> R:
    """
    Await the given coroutine after a fixed delay.

    Parameters
    ----------
    t : float
        Delay in seconds before starting the coroutine.
    coro : Awaitable[R]
        The coroutine to execute after the delay.

    Returns
    -------
    R
        The result of the awaited coroutine.

    """
    await asyncio.sleep(t)
    return await coro


async def with_jitter[R](tmin: float, tmax: float, coro: Awaitable[R]) -> R:
    """
    Await the given coroutine after a random delay within a specified range.

    Parameters
    ----------
    tmin : float
        Minimum delay in seconds.
    tmax : float
        Maximum delay in seconds.
    coro : Awaitable[R]
        The coroutine to execute after the random delay.

    Returns
    -------
    R
        The result of the awaited coroutine.

    """
    await asyncio.sleep(random.uniform(tmin, tmax))
    return await coro
