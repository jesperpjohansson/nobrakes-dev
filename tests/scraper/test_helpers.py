"""Tests for `nobrakes._scraper.helpers`."""

import asyncio
import re
import sys
import types
from unittest.mock import AsyncMock, Mock, patch

from lxml import etree
import pytest

from nobrakes._constants import FIRST_AVAILABLE_SEASON
from nobrakes._models import HashableMapping, TagSignature
from nobrakes._scraper import SVEMOScraper, helpers, pgfetch
from nobrakes.exceptions import (
    ElementError,
    UnsupportedClientError,
)

MODULEPATH = "nobrakes._scraper.helpers"


def test_import_pg_module_returns_module(monkeypatch):
    dummy_module = types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "nobrakes._scraper.pgfetch.testpg", dummy_module)

    result = SVEMOScraper._import_pg_module("testpg")
    assert result is dummy_module


def test_get_target_tags_subset_returns_correct_subset():
    tags = HashableMapping({"a": TagSignature("div"), "b": TagSignature("span")})
    result = pgfetch._get_target_tags_subset(tags, "a")
    assert result == (tags["a"],)


def test_get_hyperlin_href_returns_href():
    elem = etree.fromstring(
        """
        <td>
            <a href="http://example.com">Link</a>
        </td>
        """
    )
    assert helpers.get_hyperlink_href(elem) == "http://example.com"


class TestGetSortingIndexes:
    @staticmethod
    def test_get_sorting_indexes_returns_correct_indexes():
        tags = HashableMapping({"x": TagSignature("a"), "y": TagSignature("b")})
        indexes = pgfetch._get_sorting_indexes(tags, "x", "y")
        assert indexes == (0, 1)

    @staticmethod
    def test_get_sorting_indexes_raises_when_key_is_not_in_mapping():
        tags = HashableMapping({"key_A": TagSignature("a")})
        exc_msg = "Invalid label in '*data'."
        with pytest.raises(ValueError, match=re.escape(exc_msg)):
            pgfetch._get_sorting_indexes(tags, "key_B")


class TestValidateLaunchArgs:
    @staticmethod
    def test_does_not_raise_when_args_are_valid():
        seasons = (FIRST_AVAILABLE_SEASON,)
        tier = next(iter(helpers._AVAILABLE_TIERS))
        language = next(iter(helpers._AVAILABLE_LANGUAGES))
        helpers.validate_launch_args(seasons, tier, language)

    @staticmethod
    @pytest.mark.parametrize(
        "seasons", [(), (FIRST_AVAILABLE_SEASON, FIRST_AVAILABLE_SEASON - 1)]
    )
    def test_raises_if_args_are_invalid(seasons):
        tier = "S1"
        language = "EN"
        with pytest.raises(ExceptionGroup) as exc_group:
            helpers.validate_launch_args(seasons, tier, language)

        excs = exc_group.value.exceptions
        assert str(exc_group.value).startswith("Invalid launch arg")
        assert [type(e) for e in excs] == 3 * [ValueError]

        if seasons:
            unavailable = sorted(filter(lambda s: s < FIRST_AVAILABLE_SEASON, seasons))
            assert str(excs[0]) == f"Unavailable seasons: {unavailable}"
        else:
            assert str(excs[0]) == "'*seasons' is empty."

        assert str(excs[1]) == f"Unavailable tier: {tier}"
        assert str(excs[2]) == f"Unavailable language: {language}"


class TestCreateNestedPgTasks:
    @staticmethod
    @pytest.mark.asyncio
    async def test_returns_expected_value():
        mock_pg_module = Mock()
        mock_pg_module.fetch = AsyncMock(return_value="result")
        mock_session = Mock()
        async with asyncio.TaskGroup() as tg:
            tasks = helpers.create_nested_pg_tasks(
                pg_module=mock_pg_module,
                tg=tg,
                session=mock_session,
                urls=["http://example.com"],
                delay=None,
                jitter=None,
            )

        assert len(tasks) == 1
        result = tasks[0].result()
        assert result == "result"

    @staticmethod
    @pytest.mark.asyncio
    async def test_coro_is_called_with_delay():
        mock_pg_module = Mock()
        mock_pg_module.fetch = Mock()
        mock_session = Mock()
        with patch(
            f"{MODULEPATH}.with_delay", new_callable=AsyncMock
        ) as mock_delay_func:
            async with asyncio.TaskGroup() as tg:
                _ = helpers.create_nested_pg_tasks(
                    pg_module=mock_pg_module,
                    tg=tg,
                    session=mock_session,
                    urls=["http://example.com"],
                    delay=1,
                    jitter=None,
                )
            mock_delay_func.assert_called_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_coro_is_called_with_jitter():
        mock_pg_module = Mock()
        mock_pg_module.fetch = Mock()
        mock_session = Mock()
        with patch(
            f"{MODULEPATH}.with_jitter", new_callable=AsyncMock
        ) as mock_jitter_func:
            async with asyncio.TaskGroup() as tg:
                _ = helpers.create_nested_pg_tasks(
                    pg_module=mock_pg_module,
                    tg=tg,
                    session=mock_session,
                    urls=["http://example.com"],
                    delay=None,
                    jitter=(0, 1),
                )
            mock_jitter_func.assert_called_once()


class TestGetFilteredColumnData:
    @staticmethod
    def test_returns_expected_values():
        table = etree.fromstring(
            """
            <table>
                <tbody>
                    <tr><td>R1C1</td><td>R1C2</td></tr>
                    <tr><td>R2C1</td><td>R2C2</td></tr>
                    <tr><td>R3C1</td><td>R3C2</td></tr>
                </tbody>
            </table>
        """
        )

        pred = {1: lambda s: int(s[1]) > 1}
        extr = {1: lambda el: el.text, 2: lambda el: el.text[::-1]}
        columns = helpers.get_filtered_column_data(table, pred, extr)
        values = list(map(tuple, columns))
        assert values == [("R2C1", "R3C1"), ("2C2R", "2C3R")]

    @staticmethod
    def test_raises_when_table_has_no_tbody():
        table = etree.fromstring("<table></table>")
        with pytest.raises(ElementError):
            list(helpers.get_filtered_column_data(table, {}, {}))


class TestSessionAdapterFactory:
    @staticmethod
    @pytest.mark.parametrize(
        ("module_name", "client_name"),
        [("aiohttp", "NotClientSession"), ("notaiohttp", "ClientSession")],
    )
    def test_raises_if_adaptee_is_not_supported(module_name, client_name):
        class DummySession:
            __module__ = module_name

        DummySession.__name__ = client_name

        with pytest.raises(UnsupportedClientError):
            helpers.session_adapter_factory(DummySession())

    @staticmethod
    @pytest.mark.parametrize(
        ("module_name", "client_name"),
        [("aiohttp", "ClientSession"), ("httpx", "AsyncClient")],
    )
    def test_returns_wrapped_adaptee(monkeypatch, module_name, client_name):
        class DummySession:
            __module__ = module_name

        DummySession.__name__ = client_name

        class DummyAdapter:
            def __init__(self, session):
                self.session = session

        adapter_name = f"{module_name.upper()}SessionAdapter"

        monkeypatch.setitem(
            sys.modules,
            f"nobrakes.session._concrete_adapters.{module_name}",
            types.SimpleNamespace(**{adapter_name: DummyAdapter}),
        )

        result = helpers.session_adapter_factory(DummySession())
        assert isinstance(result, DummyAdapter)
        assert isinstance(result.session, DummySession)
