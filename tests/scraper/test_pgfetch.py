"""Tests for `nobrakes._scraper.pgfetch`."""

from contextlib import contextmanager
import re
from typing import get_args
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from lxml import etree
import pytest

from nobrakes._models import HashableMapping
from nobrakes._scraper import pgfetch
from nobrakes._scraper.pgfetch import (
    attendance,
    events,
    home,
    results,
    rider_averages,
    scorecard,
    squad,
    standings,
    teams,
)
from nobrakes.exceptions import (
    ElementError,
    FetchError,
    TablePageLimitError,
)
from nobrakes.typing._typing import TabPgModuleLabel
from tests.conftest import normalize_markup, normalize_url

SUBPKGPATH = "nobrakes._scraper.pgfetch"


@pytest.fixture
def named_target_tags() -> HashableMapping:
    return HashableMapping(
        {"label1": "element1", "label2": "element2", "label3": "element3"}
    )


@pytest.fixture
def labels_accumulated_order(named_target_tags):
    return list(named_target_tags.keys())


@pytest.fixture
def elements_accumulated_order(named_target_tags):
    return list(named_target_tags.values())


@pytest.mark.asyncio
async def test_extract_elements_raises_when_element_is_missing(
    named_target_tags,
    make_mock_session,
    labels_accumulated_order,
    elements_accumulated_order,
):
    missing_element = elements_accumulated_order.pop(1)

    mock_session = make_mock_session()

    mock_accumulator = Mock()
    mock_accumulator.remaining = (missing_element,)
    mock_accumulator.aiter_feed = AsyncMock(return_value=elements_accumulated_order)

    with (
        patch(f"{SUBPKGPATH}.ElementAccumulator", return_value=mock_accumulator),
        pytest.raises(ElementError, match="Expected 3 elements, found 2."),
    ):
        _ = await pgfetch.extract_elements(
            mock_session,
            "https://example.com",
            named_target_tags,
            *labels_accumulated_order,
        )


@pytest.mark.asyncio
async def test_extract_elements_returns_elements(named_target_tags, make_mock_session):
    mock_session = make_mock_session()
    data_labels = list(named_target_tags.keys())
    mock_elements = list(named_target_tags.values())

    mock_accumulator = Mock()
    mock_accumulator.remaining = ()
    mock_accumulator.aiter_feed = AsyncMock(return_value=mock_elements)

    with patch(f"{SUBPKGPATH}.ElementAccumulator", return_value=mock_accumulator):
        result = await pgfetch.extract_elements(
            mock_session,
            "https://example.com",
            named_target_tags,
            *data_labels,
        )

    assert result == named_target_tags._wrapped


@pytest.mark.parametrize(
    ("module", "filename", "labels"),
    [
        (attendance, "attendance_2012", ("average", "table")),
        (rider_averages, "rider_averages_2012", ("table",)),
        (scorecard, "scorecard_pir_ham_2012", ("result", "attendance", "scorecard")),
        (squad, "squad_vet_2012", ("riders", "guests")),
        (standings, "standings_2012", ("po1", "po2", "po3", "regular")),
        (teams, "teams_2012", ("table",)),
    ],
)
@pytest.mark.asyncio
async def test_fetch_finds_nodes(
    load_markup, load_pgfetch_output, make_mock_session, module, filename, labels
):
    mock_session = make_mock_session(get={"markup": load_markup(filename)})

    expected_output = load_pgfetch_output(filename)
    normalized_expected_output = {
        k: normalize_markup(v) for k, v in expected_output.items()
    }

    actual_output = await module.fetch(mock_session, "http://example.com", *labels)
    normalized_actual_output = {
        k: normalize_markup(etree.tostring(v)) for k, v in actual_output.items()
    }

    assert normalized_actual_output == normalized_expected_output


class TestFetchHome:
    @staticmethod
    @pytest.fixture
    def patch_local_func():
        @contextmanager
        def _patch_local_func(target, *args, **kwargs):
            with patch(f"{SUBPKGPATH}.home.{target}", *args, **kwargs):
                yield

        return _patch_local_func

    @staticmethod
    @pytest.fixture
    def patched_fetch(patch_local_func):
        mock_extract_elements = AsyncMock(return_value={"navbar": "navbar"})
        mock_select_accordion = Mock(return_value="accordion")
        mock_session = Mock()
        url = "http://example.com"
        season = 2025
        tier = 1

        with (
            patch_local_func("extract_elements", mock_extract_elements),
            patch_local_func("_select_accordion", mock_select_accordion),
        ):
            yield home.fetch(mock_session, url, season, tier=tier)

    @staticmethod
    @pytest.mark.parametrize("key", ["results", "previous_results"])
    def test_select_accordion_raises_if_accordion_is_not_found(key, patch_local_func):
        mock_element = Mock()
        exc_msg = (
            f"Failed selecting the {key.replace('_', ' ')} "
            "accordion in the navigation bar."
        )
        with (
            patch_local_func("xpath.first_element_e", Mock(side_effect=ElementError)),
            pytest.raises(FetchError, match=re.escape(exc_msg)),
        ):
            home._select_accordion(mock_element, key)

    @staticmethod
    def test_extract_previous_season_urls_raises_if_not_season(patch_local_func):
        exc_msg = "Failed to extract season from hyperlink text."
        with (
            patch_local_func("xpath.string", Mock(return_value=None)),
            pytest.raises(ElementError, match=re.escape(exc_msg)),
        ):
            next(home._extract_previous_season_urls([Mock()], []))

    @staticmethod
    def test_extract_previous_season_urls_raises_if_href_is_none(patch_local_func):
        tier_alias = "League Name"

        def mock_xpath_string(_, selector):
            return None if tier_alias in selector else "season"

        exc_msg = "Failed to extract URL from hyperlink href."
        with (
            patch_local_func("xpath.string", mock_xpath_string),
            pytest.raises(ElementError, match=re.escape(exc_msg)),
        ):
            next(home._extract_previous_season_urls([Mock()], [tier_alias]))

    @staticmethod
    def test_extract_previous_season_urls_raises_if_season_is_not_convertible_to_int(
        patch_local_func,
    ):
        season = "twentytwenty"
        exc_msg = f'Failed converting season "{season}" to integer.'
        with (
            patch_local_func("xpath.string", Mock(return_value=season)),
            pytest.raises(ElementError, match=re.escape(exc_msg)),
        ):
            next(home._extract_previous_season_urls([Mock()], ["Elitserien"]))

    @staticmethod
    def test_extract_current_season_url_raises_if_current_season_url_is_not_found(
        patch_local_func,
    ):
        tier_aliases = ["Elitserien"]
        exc_msg = f"Could not select any href using tier aliases: {tier_aliases}"

        with (
            patch_local_func("xpath.string", Mock(return_value=None)),
            pytest.raises(ElementError, match=re.escape(exc_msg)),
        ):
            home._extract_current_season_url(Mock(), tier_aliases)

    @staticmethod
    def test_raise_if_unavailable_raises_if_seasons_are_unavailable():
        """Test that unavailable seasons trigger a ValueError with the correct list."""
        low_bound = 2011
        high_bound = 2023
        seasons = [2025, 2010, 2011, 2023, 2024]

        with pytest.raises(
            ValueError, match=re.escape("Unavailable seasons: [2010, 2024, 2025]")
        ):
            home._raise_if_unavailable(low_bound, high_bound, *seasons)

    @staticmethod
    @pytest.mark.asyncio
    async def test_fetch_raises_if_extract_previous_season_urls_raises(
        patched_fetch, patch_local_func
    ):
        exc_msg = "Failed fetching URLs to result pages of previous seasons."

        with (
            patch_local_func(
                "_extract_previous_season_urls", Mock(side_effect=Exception)
            ),
            pytest.raises(FetchError, match=re.escape(exc_msg)),
        ):
            await patched_fetch

    @staticmethod
    @pytest.mark.asyncio
    async def test_fetch_raises_if_extract_current_season_url_raises(
        patched_fetch, patch_local_func
    ):
        exc_msg = "Failed fetching the URL to the current season results page."
        with (
            patch_local_func(
                "_extract_previous_season_urls", Mock(return_value=[(2024, "url")])
            ),
            patch_local_func(
                "_extract_current_season_url", Mock(side_effect=Exception)
            ),
            pytest.raises(FetchError, match=re.escape(exc_msg)),
        ):
            await patched_fetch

    @staticmethod
    @pytest.mark.parametrize("tier", [1, 2])
    @pytest.mark.asyncio
    async def test_fetch_finds_urls(
        load_markup, load_pgfetch_output, make_mock_session, tier
    ):
        """Test that `home.fetch()` returns correct URLs for tiers 1 and 2."""
        mock_session = make_mock_session(get={"markup": load_markup("home_2025")})
        expected_output = {
            int(k): v for k, v in load_pgfetch_output(f"home_2011_2025_t{tier}").items()
        }
        seasons = tuple(range(2011, 2026))
        result = await home.fetch(
            mock_session, "http://example.com", *seasons, tier=tier
        )
        assert result == expected_output


class TestFetchResults:
    @staticmethod
    @pytest.fixture
    def patch_local_func():
        @contextmanager
        def _patch_local_func(target, *args, **kwargs):
            with patch(f"{SUBPKGPATH}.results.{target}", *args, **kwargs):
                yield

        return _patch_local_func

    @staticmethod
    @pytest.fixture
    def make_mock_extract_elements():
        def _make_mock_extract_elements(tab_panels):
            mock_tab_content = MagicMock()
            mock_tab_content.findall.return_value = tab_panels
            return AsyncMock(return_value={"tab_content": mock_tab_content})

        return _make_mock_extract_elements

    @staticmethod
    @pytest.mark.asyncio
    async def test_fetch_raises_when_missing_tabs(
        patch_local_func, make_mock_extract_elements
    ):
        pg_names = ["pg1", "pg2", "pg3", "pg4", "pg5"]
        tab_panels = ["elem1", "elem2"]

        mock_session = Mock()
        mock_extract_elements = make_mock_extract_elements(tab_panels)

        exc_msg = f"Expected {len(pg_names)} tabs, found {len(tab_panels)}."
        with (
            patch_local_func("extract_elements", mock_extract_elements),
            pytest.raises(ElementError, match=re.escape(exc_msg)),
        ):
            await results.fetch(mock_session, "http://example.com", *pg_names)

    @staticmethod
    @pytest.mark.asyncio
    async def test_fetch_raises_when_url_extraction_fails(
        patch_local_func, make_mock_extract_elements
    ):
        pg_names = ["pg1", "pg2", "pg3", "pg4"]
        tab_panels = [
            {},
            {"src": "http://example.com"},
            {"href": "http://example.com"},
            {"src": ""},
        ]

        mock_session = Mock()
        mock_extract_elements = make_mock_extract_elements(tab_panels)

        exc_msg = "Failed extracting URL(s) for pages: ['pg1', 'pg4']"
        with (
            patch_local_func("extract_elements", mock_extract_elements),
            pytest.raises(ElementError, match=re.escape(exc_msg)),
        ):
            await results.fetch(mock_session, "http://example.com", *pg_names)

    @staticmethod
    @pytest.mark.asyncio
    async def test_fetch_extracts_urls(
        load_markup, load_pgfetch_output, make_mock_session
    ):
        mock_session = make_mock_session(get={"markup": load_markup("results_2012")})
        expected_output = {
            k: normalize_url(v) for k, v in load_pgfetch_output("results_2012").items()
        }
        names = get_args(TabPgModuleLabel.__value__)
        actual_output = await results.fetch(mock_session, "http://example.com", *names)
        actual_output = {k: normalize_url(v) for k, v in actual_output.items()}

        assert actual_output == expected_output


@pytest.fixture
def patch_table_browser_launch():
    mock_browser = Mock()
    mock_browser.table = etree.Element("table")

    return patch(
        "nobrakes._scraper.table_browser.TableBrowser.launch",
        AsyncMock(return_value=mock_browser),
    )


@pytest.mark.asyncio
class TestFetchEvents:
    async def test_fetch_finds_nodes(
        self, load_markup, load_pgfetch_output, make_mock_session
    ):
        filename = "events_2012"

        labels = ("table",)
        mock_session = make_mock_session(
            get={"markup": load_markup(f"{filename}_pg1")},
            post={"markup": load_markup(f"{filename}_pg2")},
        )

        expected_output = load_pgfetch_output(filename)
        normalized_expected_output = {
            k: normalize_markup(v) for k, v in expected_output.items()
        }

        actual_output = await events.fetch(mock_session, "http://example.com", *labels)
        normalized_actual_output = {
            k: normalize_markup(etree.tostring(v)) for k, v in actual_output.items()
        }

        assert normalized_actual_output == normalized_expected_output

    async def test_raises_if_pagelimit_is_exceeded(
        self, mock_session, patch_table_browser_launch
    ):
        pagelimit = 0
        exc_msg = f"Page limit ({pagelimit}) exceeded."
        with (
            patch_table_browser_launch,
            pytest.raises(TablePageLimitError, match=re.escape(exc_msg)),
        ):
            _ = await events.fetch(mock_session, "http://example.com", pagelimit=0)

    async def test_raises_if_tbody_is_not_element(
        self, mock_session, patch_table_browser_launch
    ):
        exc_msg = "<table> is missing <tbody>."
        with (
            patch_table_browser_launch,
            pytest.raises(ElementError, match=re.escape(exc_msg)),
        ):
            _ = await events.fetch(mock_session, "http://example.com")
