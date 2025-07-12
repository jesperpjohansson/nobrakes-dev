"""Tests for `nobrakes.session.utils`."""

from unittest.mock import AsyncMock, patch

import pytest

from nobrakes.session._utils import (
    DummyCookieJar,
    with_delay,
    with_jitter,
)


@pytest.mark.asyncio
async def test_dummy_cookie_jar_extracts_nothing():
    jar = DummyCookieJar()
    try:
        jar.extract_cookies(None, None)
    except Exception:
        pytest.fail("DummyCookieJar.extract_cookies should not raise exceptions.")


@pytest.mark.asyncio
async def test_with_delay_executes_after_fixed_delay():
    coro = AsyncMock(return_value="result")
    with patch("asyncio.sleep", new_callable=AsyncMock) as sleep_mock:
        result = await with_delay(1.0, coro())
        sleep_mock.assert_awaited_once_with(1.0)
        assert result == "result"


@pytest.mark.asyncio
async def test_with_jitter_executes_after_random_delay():
    coro = AsyncMock(return_value="jitter")
    with (
        patch("asyncio.sleep", new_callable=AsyncMock) as sleep_mock,
        patch("random.uniform", return_value=0.42),
    ):
        result = await with_jitter(0.0, 1.0, coro())
        sleep_mock.assert_awaited_once_with(0.42)
        assert result == "jitter"
