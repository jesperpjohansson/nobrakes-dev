"""Tests for `nobrakes._scraper.__init__`."""

from copy import deepcopy
import re
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiohttp
import httpx
import pytest
import pytest_asyncio

from nobrakes._scraper import SVEMOScraper, _ensure_data_labels, _ensure_launched
from nobrakes.exceptions import FetchError, ScraperError, UnsupportedClientError

MODULEPATH = "nobrakes._scraper"


@pytest.fixture
def initialized_scraper(mock_session) -> SVEMOScraper:
    with patch(f"{MODULEPATH}.session_adapter_factory", return_value=mock_session):
        return SVEMOScraper("session")


@pytest_asyncio.fixture
def launch_scraper(monkeypatch) -> SVEMOScraper:
    async def _launch_scraper(scraper: SVEMOScraper):
        mock_home_fetch = AsyncMock(return_value={2023: "https://example.com/2023"})
        mock_results_fetch = AsyncMock(
            return_value={"events": "https://example.com/2023/events"}
        )

        mock_home_pg_module = MagicMock(fetch=mock_home_fetch)
        mock_results_pg_module = MagicMock(fetch=mock_results_fetch)

        monkeypatch.setattr(
            f"{MODULEPATH}.SVEMOScraper._import_pg_module",
            lambda name: (
                mock_home_pg_module if name == "home" else mock_results_pg_module
            ),
        )

        return await scraper.launch(2023, tier=1, language="sv-se")

    return _launch_scraper


@pytest_asyncio.fixture
async def launched_scraper(launch_scraper, initialized_scraper) -> SVEMOScraper:
    return await launch_scraper(deepcopy(initialized_scraper))


@pytest.mark.asyncio
async def test_init_expected_state(initialized_scraper, mock_session):
    assert isinstance(initialized_scraper, SVEMOScraper)
    assert initialized_scraper._launched is False
    assert initialized_scraper._url_cache == {}
    assert initialized_scraper._pg_cache == {}
    assert initialized_scraper._session == mock_session


@pytest.mark.asyncio
async def test_init_raises_when_called_with_unsupported_session(mock_session):
    exc_msg = re.escape(
        "'MockSession' from library 'tests' is not a supported session."
    )
    with pytest.raises(UnsupportedClientError, match=exc_msg):
        _ = SVEMOScraper(mock_session)


def test_launch_sets_launched(launched_scraper):
    assert launched_scraper._launched is True


@pytest.mark.parametrize(
    ("lib", "client_name"), [(aiohttp, "ClientSession"), (httpx, "AsyncClient")]
)
@pytest.mark.asyncio
async def test_launch_updates_session_headers(launch_scraper, lib, client_name):
    expected_headers = {
        "accept": "text/html",
        "cookie": "Svemo.TA.Language.SelectedLanguage=sv-se",
    }

    async with getattr(lib, client_name)() as session:
        scraper = SVEMOScraper(session)
        await launch_scraper(scraper)
        assert not expected_headers.items() - scraper._session.headers.items()


@pytest.mark.parametrize(
    ("lib", "client_name"), [(aiohttp, "ClientSession"), (httpx, "AsyncClient")]
)
@pytest.mark.asyncio
async def test_launch_updates_url_cache(launch_scraper, lib, client_name):
    expected = {("events", 2023): "https://example.com/2023/events"}

    async with getattr(lib, client_name)() as session:
        scraper = SVEMOScraper(session)
        await launch_scraper(scraper)
        assert scraper._url_cache == expected


@pytest.mark.asyncio
async def test_launch_raises_if_called_twice(initialized_scraper):
    initialized_scraper._launched = True
    with pytest.raises(ScraperError, match=re.escape("already been launched")):
        await initialized_scraper.launch(2023)


@pytest.mark.asyncio
async def test_launch_raises_if_results_pg_url_fetch_fails(initialized_scraper):
    exc_msg = re.escape("Failed fetching results page URLs from the home page.")
    with (
        pytest.raises(FetchError, match=exc_msg),
        patch.object(
            initialized_scraper, "_import_pg_module", AsyncMock(side_effect=Exception())
        ),
    ):
        await initialized_scraper.launch(2023)


@pytest.mark.asyncio
async def test_launch_raises_if_tab_pg_url_fetch_fails(initialized_scraper):
    def mock_import_pg_module(name: str):
        mock_module = Mock()
        mock_fetch = AsyncMock()
        mock_module.fetch = mock_fetch

        if name == "home":
            mock_fetch.return_value = {2025: "https://example.com"}
        else:
            mock_fetch.side_effect = Exception()

        return mock_module

    exc_msg = re.escape("Failed fetching URLs from all results pages.")
    with (
        pytest.raises(FetchError, match=exc_msg),
        patch.object(SVEMOScraper, "_import_pg_module", mock_import_pg_module),
    ):
        await initialized_scraper.launch(2023)


@pytest.mark.asyncio
async def test__fetch_tab_pg_data_returns_expected_items(launched_scraper):
    expected = {"K", "V"}

    with patch(f"{MODULEPATH}.SVEMOScraper._import_pg_module") as mock_import_pg_module:
        mock_pg_module = Mock()
        mock_pg_module.fetch = AsyncMock(return_value=expected)
        mock_import_pg_module.return_value = mock_pg_module

        result = await launched_scraper._fetch_tab_pg_data(
            "label", season=2023, pg="events"
        )
        assert result == expected


@pytest.mark.asyncio
async def test__fetch_tab_pg_data_raises_if_unavailable_season(
    initialized_scraper, launch_scraper
):
    await launch_scraper(initialized_scraper)
    with pytest.raises(
        ScraperError,
        match=re.escape("The events page URL for season 2025 is unavailable."),
    ):
        _ = await initialized_scraper._fetch_tab_pg_data(
            "label", pg="events", season=2025
        )


@pytest.mark.asyncio
async def test__fetch_tab_pg_data_raises_when_fetch_fails(initialized_scraper):
    test_season = 2025
    test_pg = "events"
    test_url = "https://example.com"
    initialized_scraper._url_cache = {(test_pg, test_season): test_url}
    initialized_scraper._launched = True
    fetch_exception = RuntimeError("Simulated failure")

    with patch(f"{MODULEPATH}.SVEMOScraper._import_pg_module") as mock_import_pg_module:
        mock_pg_module = Mock()
        mock_pg_module.fetch = AsyncMock(side_effect=fetch_exception)
        mock_import_pg_module.return_value = mock_pg_module
        with pytest.raises(FetchError, match=re.escape("Failed fetching page data.")):
            await initialized_scraper._fetch_tab_pg_data(
                "label", season=test_season, pg=test_pg
            )


@pytest.mark.asyncio
async def test__fetch_nested_pg_data_returns_expected_items(launched_scraper):
    fallback = AsyncMock(return_value={"table": MagicMock()})

    key_columns = [["2025-05-01", "2025-05-02"], ["Team A", "Team B"]]
    href_column = ["/1", "/2"]
    full_columns = [*key_columns, href_column]

    with (
        patch(f"{MODULEPATH}.get_filtered_column_data", return_value=full_columns),
        patch(f"{MODULEPATH}.TA_DOMAIN", "https://example.com"),
        patch(f"{MODULEPATH}.create_nested_pg_tasks") as mock_create_tasks,
        patch(f"{MODULEPATH}.is_element", return_value=True),
    ):
        fake_task_1 = MagicMock()
        fake_task_1.result.return_value = {"K1": "ELEMENT1"}

        fake_task_2 = MagicMock()
        fake_task_2.result.return_value = {"K2": "ELEMENT2"}

        mock_create_tasks.return_value = [fake_task_1, fake_task_2]

        result = await launched_scraper._fetch_nested_pg_data(
            "some_label",
            cache_key=("events", 2025),
            fallback=fallback(),
            pg_module=MagicMock(),
            col_predicates={},
            col_extractors={},
            key_builder=lambda keys: tuple(keys),
            delay=None,
            jitter=None,
        )

        assert result == {
            ("2025-05-01", "Team A"): {"K1": "ELEMENT1"},
            ("2025-05-02", "Team B"): {"K2": "ELEMENT2"},
        }


@pytest.mark.asyncio
async def test__fetch_nested_pg_data_raises_when_fetch_fails(launched_scraper):
    fallback = AsyncMock(return_value={"table": MagicMock()})
    exc_msg = "Failed fetching data from page(s)."
    with (
        patch(
            f"{MODULEPATH}.get_filtered_column_data",
            return_value=[["2025"], ["Team A"], ["https://example.com/scorecard"]],
        ),
        patch(f"{MODULEPATH}.TA_DOMAIN", "https://example.com"),
        patch(
            f"{MODULEPATH}.create_nested_pg_tasks",
            side_effect=ExceptionGroup("group", [RuntimeError("fail")]),
        ),
        patch(f"{MODULEPATH}.is_element", return_value=True),
        pytest.raises(FetchError, match=re.escape(exc_msg)),
    ):
        await launched_scraper._fetch_nested_pg_data(
            "label",
            cache_key=("events", 2025),
            fallback=fallback(),
            pg_module=MagicMock(),
            col_predicates={},
            col_extractors={},
            key_builder=lambda: ...,
            delay=None,
            jitter=None,
        )


@pytest.mark.asyncio
async def test__fetch_nested_pg_data_raises_when_cached_table_is_not_an_element(
    launched_scraper,
):
    fallback = AsyncMock(return_value={"table": "not_an_element"})
    exc_msg = "Unexpected cached/fetched table type: <class 'str'>"
    with (
        patch(
            f"{MODULEPATH}.get_filtered_column_data",
            return_value=[["2025"], ["Team A"], ["https://example.com/scorecard"]],
        ),
        patch(f"{MODULEPATH}.TA_DOMAIN", "https://example.com"),
        pytest.raises(RuntimeError, match=re.escape(exc_msg)),
    ):
        await launched_scraper._fetch_nested_pg_data(
            "label",
            cache_key=("events", 2025),
            fallback=fallback(),
            pg_module=MagicMock(),
            col_predicates={},
            col_extractors={},
            key_builder=lambda: ...,
            delay=None,
            jitter=None,
        )


@pytest.mark.asyncio
async def test__ensure_launched_raises_when_not_launched(initialized_scraper):
    initialized_scraper._launched = False

    @_ensure_launched
    async def decorated_method(_):
        pass

    with pytest.raises(ScraperError):
        _ = await decorated_method(initialized_scraper)


@pytest.mark.asyncio
async def test__ensure_launched_does_not_raise_when_launched(initialized_scraper):
    initialized_scraper._launched = True

    @_ensure_launched
    async def decorated_method(_):
        pass

    await decorated_method(initialized_scraper)


@pytest.mark.asyncio
async def test__ensure_data_labels_raises_data_is_empty(initialized_scraper):
    @_ensure_data_labels
    async def decorated_method(_, *data, **kwargs):
        pass

    with pytest.raises(ValueError, match=re.escape("'*data' is empty.")):
        _ = await decorated_method(initialized_scraper, kwarg="value")


@pytest.mark.asyncio
async def test__ensure_launched_does_not_raise_when_data_is_not_empty(
    initialized_scraper,
):
    @_ensure_data_labels
    async def decorated_method(_, *data, **kwargs):
        pass

    await decorated_method(initialized_scraper, "label", kwarg="value")


@pytest.mark.parametrize("pg", ["events", "teams"])
@pytest.mark.asyncio
async def test_get_method_updates_pg_cache(monkeypatch, launched_scraper, pg):
    launched_scraper._url_cache[(pg, 2022)] = "https://example.com"

    mock_pg_module = Mock()
    mock_pg_module.fetch = AsyncMock(return_value={"table": "markup"})
    monkeypatch.setattr(
        f"{MODULEPATH}.SVEMOScraper._import_pg_module", lambda _: mock_pg_module
    )

    method = getattr(launched_scraper, pg)
    await method(season=2022, cache=True)
    assert (pg, 2022) in launched_scraper._pg_cache
    assert launched_scraper._pg_cache[(pg, 2022)] == {"table": "markup"}


@pytest.mark.parametrize(
    ("method_name", "location", "data_labels"),
    [
        ("events", "tab", ()),
        ("standings", "tab", ("label",)),
        ("teams", "tab", ()),
        ("rider_averages", "tab", ()),
        ("attendance", "tab", ("label",)),
        ("scorecards", "nested", ("label",)),
        ("squads", "nested", ("label",)),
    ],
)
@pytest.mark.asyncio
async def test_get_method_returns_pg_data(
    monkeypatch, initialized_scraper, method_name, location, data_labels
):
    method = getattr(initialized_scraper, method_name)

    if method_name == "scorecards":
        monkeypatch.setattr(f"{MODULEPATH}.SVEMOScraper.events", Mock())

    if method_name == "squads":
        monkeypatch.setattr(f"{MODULEPATH}.SVEMOScraper.teams", Mock())

    with patch(
        f"{MODULEPATH}.SVEMOScraper._fetch_{location}_pg_data", AsyncMock()
    ) as mock_fetch:
        mock_fetch.return_value = method_name
        assert await method(*data_labels, season=2011) == method_name
