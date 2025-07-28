"""Tests for `nobrakes.client.utils`."""

from unittest.mock import AsyncMock, patch

import pytest

from nobrakes.client._utils import (
    DummyCookieJar,
    with_delay,
    with_jitter,
)


@pytest.mark.asyncio
async def test_dummy_cookie_jar_extracts_nothing():
    assert DummyCookieJar().extract_cookies() is None


@pytest.mark.asyncio
class TestSleepFuncs:
    @pytest.fixture
    def mock_sleep(self):
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock:
            yield mock

    async def test_with_delay_executes_after_fixed_delay(self, mock_sleep):
        coro = AsyncMock(return_value="result")
        result = await with_delay(1.0, coro())
        mock_sleep.assert_awaited_once_with(1.0)
        assert result == "result"

    async def test_with_jitter_executes_after_random_delay(self, mock_sleep):
        coro = AsyncMock(return_value="jitter")
        with patch("random.uniform", return_value=0.42):
            result = await with_jitter(0.0, 1.0, coro())

        mock_sleep.assert_awaited_once_with(0.42)
        assert result == "jitter"
