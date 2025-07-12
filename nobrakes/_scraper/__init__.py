"""Subpackage dedicated to implementing `SVEMOScraper`."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from functools import wraps
import importlib
from typing import TYPE_CHECKING, Concatenate, Literal, Self, cast, get_args, overload

from nobrakes._constants import HOME_DOMAIN, TA_DOMAIN
from nobrakes._element_utils import string
from nobrakes._scraper.helpers import (
    create_nested_pg_tasks,
    get_filtered_column_data,
    get_hyperlink_href,
    session_adapter_factory,
    validate_launch_args,
)
from nobrakes.exceptions import FetchError, ScraperError
from nobrakes.session._base import SessionAdapter
from nobrakes.typing._typing import (
    URL,
    PgCache,
    PgFetchModuleProtocol,
    TabPgModuleLabel,
    URLCache,
    is_element,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from nobrakes import pgelements
    from nobrakes.typing import (
        AttendancePgDataLabel,
        ETreeElement,
        EventsPgDataLabel,
        Language,
        RiderAveragesPgDataLabel,
        ScorecardPgDataLabel,
        SquadPgDataLabel,
        StandingsPgDataLabel,
        SupportedClient,
        TeamsPgDataLabel,
        Tier,
    )

__all__ = ["SVEMOScraper"]


def _ensure_launched[T: SVEMOScraper, **P, R](
    func: Callable[Concatenate[T, P], R],
) -> Callable[Concatenate[T, P], R]:
    """Raise `ScrapingError` if `SVEMOScraper.launch()` has not been called."""

    @wraps(func)
    def wrapper(self: T, *args: P.args, **kwargs: P.kwargs) -> R:
        if not self._launched:
            exc_msg = "The scraper has not been launched."
            raise ScraperError(exc_msg)

        return func(self, *args, **kwargs)

    return cast("Callable[Concatenate[T, P], R]", wrapper)


def _ensure_data_labels[T: SVEMOScraper, **P, R](
    func: Callable[Concatenate[T, P], R],
) -> Callable[Concatenate[T, P], R]:
    """Raise `ValueError` if no page data labels have been passed."""

    @wraps(func)
    def wrapper(self: T, *data: P.args, **kwargs: P.kwargs) -> R:
        if not data:
            exc_msg = "'*data' is empty."
            raise ValueError(exc_msg)

        return func(self, *data, **kwargs)

    return cast("Callable[Concatenate[T, P], R]", wrapper)


class SVEMOScraper:
    """
    An asynchronous scraper for SVEMO speedway data.

    This class provides methods to fetch structured HTML data from different pages
    of the SVEMO website.

    Parameters
    ----------
    session : SupportedClient
        An instance of `nobrakes.SessionAdapter` or any of the following supported
        third-party clients:
        - `aiohttp.ClientSession`
        - `httpx.AsyncClient`

    Raises
    ------
    UnsupportedClientError
        If `session` is an unsupported client.

    """

    def __init__(self, session: SupportedClient) -> None:
        self._launched = False
        self._url_cache: URLCache = {}
        self._pg_cache: PgCache = {}

        self._session: SessionAdapter = (
            session
            if isinstance(session, SessionAdapter)
            else session_adapter_factory(session)
        )

    async def launch(
        self,
        *seasons: int,
        tier: Tier = 1,
        language: Language = "sv-se",
    ) -> Self:
        """
        Fetch required URLs and adds them to the internal URL cache.

        Parameters
        ----------
        *seasons : int
            Seasons to scrape. From 2011 and onwards.
        tier : Tier, default 1
            The league tier to scrape, by default 1.
            - 1 : Bauhausligan/Elitserien
            - 2 : Allsvenskan.
        language : Language, default "sv-se"
            Language header.
            - "sv-se" - Swedish
            - "en-us" - English

        Returns
        -------
        Self
            A ready-to-use instance of SVEMOScraper.

        Raises
        ------
        ExceptionGroup
            If one or more of the input arguments are invalid (unsupported
            season, tier, or language).
        ScrapingError
            If the scraper has already been launched.
        FetchError
            If not all page URLs could be fetched.

        """
        if self._launched:
            exc_msg = "The scraper has already been launched."
            raise ScraperError(exc_msg)

        validate_launch_args(seasons, tier, language)

        self._session.headers.update(
            {
                "accept": "text/html",
                "cookie": f"Svemo.TA.Language.SelectedLanguage={language}",
            },
        )

        home_pg_module: PgFetchModuleProtocol[dict[int, URL]] = (
            SVEMOScraper._import_pg_module("home")
        )
        results_pg_module: PgFetchModuleProtocol[dict[TabPgModuleLabel, URL]] = (
            SVEMOScraper._import_pg_module("results")
        )

        try:
            results_pg_urls = await home_pg_module.fetch(
                self._session,
                URL(HOME_DOMAIN),
                *seasons,
                tier=tier,
            )
        except Exception as exc:
            exc_msg = "Failed fetching results page URLs from the home page."
            raise FetchError(exc_msg) from exc

        names = get_args(TabPgModuleLabel.__value__)  # pylint: disable=no-member
        try:
            async with asyncio.TaskGroup() as tg:
                tasks = {
                    key: tg.create_task(
                        results_pg_module.fetch(self._session, url, *names),
                    )
                    for key, url in results_pg_urls.items()
                }
        except Exception as exc:
            exc_msg = "Failed fetching URLs from all results pages."
            raise FetchError(exc_msg) from exc

        self._url_cache |= {
            (pg, key): URL(url)
            for key, task in tasks.items()
            for pg, url in task.result().items()
        }

        self._launched = True
        return self

    async def events(
        self,
        *,
        season: int,
        cache: bool = False,
        pagesize: int = 50,
        pagelimit: int = 5,
    ) -> pgelements.Events:
        """
        Fetch events page data for a given season.

        Parameters
        ----------
        season : int
            The season to fetch data for.
        cache : bool, default False
            Whether or not to add the fetched data to the cache.
        pagesize : int, default 50
            Number of rows per page, by default 50.
        pagelimit : int, default 5
            Maximum number of expected pages, by default 5.

        Returns
        -------
        pgelements.Events
            Parsed page data.

        Raises
        ------
        ValueError
            If `season` was not passed when the session was launched.
        FetchError
            If the page data could not be fetched.
        TablePageLimitError
            If the number of table pages exceeds `pagelimit`.


        See Also
        --------
        scorecards : Uses cached data.

        Notes
        -----
        Under normal circumstances, `pagesize` and `pagelimit` are best left alone.


        """
        return await self._fetch_tab_pg_data(
            "table",
            pg="events",
            season=season,
            cache=cache,
            pagesize=pagesize,
            pagelimit=pagelimit,
        )

    async def standings(
        self,
        *data: StandingsPgDataLabel,
        season: int,
    ) -> pgelements.Standings:
        """
        Fetch standings data for a given season.

        Parameters
        ----------
        *data : StandingsPgDataLabel
            Page data to extract.
            - "po1" - Results from the finals.
            - "po2" - Results from the semifinals, or equivalent.
            - "po3" - Results from the semifinals, or equivalent.
            - "regular" - The regular season table.
        season : int
            Target season.

        Returns
        -------
        pgelements.Standings
            Parsed page data.

        Raises
        ------
        ValueError
            If `*data` is empty.
            If `season` was not passed when the session was launched.
        FetchError
            If the page data could not be fetched.

        Notes
        -----
        Due to changes to the play-off format, some pages will have less than
        three race off sections.

        """
        return await self._fetch_tab_pg_data(*data, pg="standings", season=season)

    async def teams(self, *, season: int, cache: bool = False) -> pgelements.Teams:
        """
        Fetch team information for a given season.

        Parameters
        ----------
        season : int
            Target season.
        cache : bool, default False
            Whether or not to add the fetched data to the cache.

        Returns
        -------
        pgelements.Teams
            Parsed page data.

        Raises
        ------
        ValueError
            If `season` was not passed when the session was launched.
        FetchError
            If the page data could not be fetched.

        See Also
        --------
        squads : Uses cached data.

        """
        return await self._fetch_tab_pg_data(
            "table",
            pg="teams",
            season=season,
            cache=cache,
        )

    async def rider_averages(self, *, season: int) -> pgelements.RiderAverages:
        """
        Fetch a table containing rider averages for a given season.

        Parameters
        ----------
        season : int
            Target season.

        Returns
        -------
        pgelements.RiderAverages
            Parsed page data.

        Raises
        ------
        ValueError
            If `season` was not passed when the session was launched.
        FetchError
            If the page data could not be fetched.

        """
        return await self._fetch_tab_pg_data(
            "table",
            pg="rider_averages",
            season=season,
        )

    async def attendance(
        self,
        *data: AttendancePgDataLabel,
        season: int,
    ) -> pgelements.Attendance:
        """
        Fetch attendance data for a given season.

        Parameters
        ----------
        *data : AttendancePgDataLabel
            Page data to extract.
            - "average" - The average attendance figure.
            - "table" - Attendance figures by event.
        season : int
            Target season.

        Returns
        -------
        pgelements.Attendance
            Parsed page data.

        Raises
        ------
        ValueError
            If `*data` is empty.
            If `season` was not passed when the session was launched.
        FetchError
            If the page data could not be fetched.

        """
        return await self._fetch_tab_pg_data(*data, pg="attendance", season=season)

    async def scorecards(
        self,
        *data: ScorecardPgDataLabel,
        season: int,
        date_query: Callable[[str], bool] | None = None,
        name_query: Callable[[str], bool] | None = None,
        delay: float | None = None,
        jitter: tuple[float, float] | None = None,
        **events_pg_kwargs,
    ) -> dict[tuple[str, str], pgelements.Scorecard]:
        """
        Fetch scorecard details for a given season.

        The pages are accessed through links found in the table of a events
        page. If a call to `events` has previously been made, with parameter
        `cache` set to `True`, the cached table will be used.

        Parameters
        ----------
        *data : ScorecardPgDataLabel
            Page data to extract.
            - "result" - Team names and points.
            - "attendance" - The attendance figure.
            - "table" - A scorecard containing heat data.
        season : int
            Target season.
        date_query : Callable[[str], bool], optional
            A predicate function to filter table rows based on first column.
            The input is a string in the format returned by the source site.
        name_query : Callable[[str], bool], optional
            A predicate function to filter table rows based on second column.
            The input is a string in the format returned by the source site.
        delay : float, optional
            Delay applied before each fetch, in seconds.
        jitter : tuple[float, float], optional
            Tuple representing random jitter range (min, max) applied before
            each fetch, in seconds.
        **events_pg_kwargs : Any
            Keyword arguments forwarded to `events`. Redundant when a cached
            table is used.

        Raises
        ------
        ValueError
            If `*data` is empty.
            If `season` was not passed when the session was launched.
        FetchError
            If the events page data could not be fetched.
            If data from one or more scorecard pages could not be fetched.

        Returns
        -------
        dict[tuple[str, str], pgelements.Scorecard]
            Mapping of (date, name) to their parsed scorecard data.

        """
        return await self._fetch_nested_pg_data(
            *data,
            cache_key=("events", season),
            fallback=self.events(season=season, **events_pg_kwargs),
            pg_module=SVEMOScraper._import_pg_module("scorecard"),
            col_predicates=(
                # User defined predicates applied to key (ID) columns.
                {
                    i: q
                    for i, q in zip((1, 2), (date_query, name_query), strict=False)
                    if q
                }
                # Retains rows with links.
                | {3: lambda s: s in {"Matchresultat", "Matchresults"}}
            ),
            col_extractors=dict(
                enumerate(
                    (
                        string.stripped_text_e,
                        string.stripped_text_e,
                        get_hyperlink_href,
                    ),
                    1,
                ),
            ),
            key_builder=lambda keys: (keys[0], keys[1]),
            delay=delay,
            jitter=jitter,
        )

    async def squads(
        self,
        *data: SquadPgDataLabel,
        season: int,
        team_query: Callable[[str], bool] | None = None,
        delay: float | None = None,
        jitter: tuple[float, float] | None = None,
        **teams_pg_kwargs,
    ) -> dict[str, pgelements.Squad]:
        """
        Fetch squads for each team for a given season.

        The pages are accessed through links found in the table of a teams page.
        If a call to `teams()` has previously been made, with parameter
        `cache` set to `True`, the cached table will be used.

        Parameters
        ----------
        *data : SquadPgDataLabel
            Page data to extract.
            - "riders" - A table containing information about non-guest riders.
            - "guests" - A table containing information about guest riders.
        season : int
            Target season.
        team_query : Callable[[str], bool], optional
            A predicate function to filter table rows based on first column.
            The input is a string in the format returned by the source site.
        delay : float, optional
            Delay applied between each request, in seconds.
        jitter : tuple[float, float], optional
            Tuple representing random jitter range (min, max) applied before
            each fetch, in seconds.
        **teams_pg_kwargs : Any
            Keyword arguments forwarded to `teams`. Redundant when a cached table
            is used.

        Returns
        -------
        dict[str, pgelements.Squad]]
            Mapping of team names to parsed squad data.

        Raises
        ------
        ValueError
            If `*data` is empty.
            If `season` was not passed when the session was launched.
        FetchError
            If the teams page data could not be fetched.
            If data from one or more squad pages could not be fetched.

        """
        return await self._fetch_nested_pg_data(
            *data,
            cache_key=("teams", season),
            fallback=self.teams(season=season, **teams_pg_kwargs),
            pg_module=SVEMOScraper._import_pg_module("squad"),
            col_predicates=(
                # User defined query applied to the key (ID) column.
                ({1: team_query} if team_query else {})
                # Retains rows with links.
                | {4: lambda s: s in {"Visa", "View"}}
            ),
            col_extractors=dict(
                zip((1, 4), (string.stripped_text_e, get_hyperlink_href), strict=False),
            ),
            key_builder=lambda keys: keys[0],
            delay=delay,
            jitter=jitter,
        )

    @staticmethod
    def _import_pg_module(pg: str) -> PgFetchModuleProtocol:
        """Dynamically import and return a page-fetching module by name."""
        return importlib.import_module(f"nobrakes._scraper.pgfetch.{pg}")

    @overload
    async def _fetch_tab_pg_data(
        self,
        /,
        *data: EventsPgDataLabel,
        pg: Literal["events"],
        season: int,
        cache: bool,
        **kwargs,
    ) -> pgelements.Events: ...

    @overload
    async def _fetch_tab_pg_data(
        self,
        /,
        *data: StandingsPgDataLabel,
        pg: Literal["standings"],
        season: int,
        **kwargs,
    ) -> pgelements.Standings: ...

    @overload
    async def _fetch_tab_pg_data(
        self,
        /,
        *data: TeamsPgDataLabel,
        pg: Literal["teams"],
        season: int,
        cache: bool,
        **kwargs,
    ) -> pgelements.Teams: ...

    @overload
    async def _fetch_tab_pg_data(
        self,
        /,
        *data: RiderAveragesPgDataLabel,
        pg: Literal["rider_averages"],
        season: int,
        **kwargs,
    ) -> pgelements.RiderAverages: ...

    @overload
    async def _fetch_tab_pg_data(
        self,
        /,
        *data: AttendancePgDataLabel,
        pg: Literal["attendance"],
        season: int,
        **kwargs,
    ) -> pgelements.Attendance: ...

    @_ensure_launched
    @_ensure_data_labels
    async def _fetch_tab_pg_data(self, /, *data, pg, season, cache=False, **kwargs):
        """
        Fetch data from a tab-level page.

        Common mechanism for fetching data a page embedded in, or linked to in a
        results page tab.
        """
        url: URL | None = self._url_cache.get((pg, season))
        if url is None:
            formatted_pg_name = pg.replace("_", " ")
            exc_msg = (
                f"The {formatted_pg_name} page URL for season {season} is unavailable. "
                f"Verify that {season} was passed the scraper was launched."
            )
            raise ScraperError(exc_msg)

        pg_module = SVEMOScraper._import_pg_module(pg)
        try:
            elements = await pg_module.fetch(self._session, url, *data, **kwargs)
        except Exception as exc:
            scraping_exc = FetchError("Failed fetching page data.")
            scraping_exc.add_note(f"URL: {url}")
            raise scraping_exc from exc

        if cache:
            self._pg_cache[(pg, season)] = deepcopy(elements)

        return elements

    @overload
    async def _fetch_nested_pg_data(
        self,
        /,
        *data: ScorecardPgDataLabel,
        cache_key: tuple[Literal["events"], int],
        fallback: Awaitable[pgelements.Events],
        pg_module: PgFetchModuleProtocol,
        col_predicates: dict[int, Callable[[str], bool]],
        col_extractors: dict[int, Callable[[ETreeElement], str]],
        key_builder: Callable[[tuple[str, ...]], tuple[str, str]],
        delay: float | None,
        jitter: tuple[float, float] | None,
    ) -> dict[tuple[str, str], pgelements.Scorecard]: ...

    @overload
    async def _fetch_nested_pg_data(
        self,
        /,
        *data: SquadPgDataLabel,
        cache_key: tuple[Literal["teams"], int],
        fallback: Awaitable[pgelements.Teams],
        pg_module: PgFetchModuleProtocol,
        col_predicates: dict[int, Callable[[str], bool]],
        col_extractors: dict[int, Callable[[ETreeElement], str]],
        key_builder: Callable[[tuple[str, ...]], str],
        delay: float | None,
        jitter: tuple[float, float] | None,
    ) -> dict[str, pgelements.Squad]: ...

    @_ensure_launched
    @_ensure_data_labels
    async def _fetch_nested_pg_data(
        self,
        /,
        *data,
        cache_key,
        fallback,
        pg_module,
        col_predicates,
        col_extractors,
        key_builder,
        delay,
        jitter,
    ):
        """
        Fetch data from multiple pages accessed via a table in a tab-level page.

        Common mechanism for fetching data from pages that are accessed through
        hyperlinks in a table column.
        """
        table = (self._pg_cache.get(cache_key) or await fallback).get("table")

        if not is_element(table):
            exc_msg = f"Unexpected cached/fetched table type: {type(table)}."
            raise RuntimeError(exc_msg)

        *key_columns, href_column = await asyncio.to_thread(
            get_filtered_column_data,
            table,
            col_predicates,
            col_extractors,
        )

        urls = (URL(f"{TA_DOMAIN}{href}") for href in href_column)

        try:
            async with asyncio.TaskGroup() as tg:
                tasks = create_nested_pg_tasks(
                    *data,
                    pg_module=pg_module,
                    tg=tg,
                    session=self._session,
                    urls=urls,
                    delay=delay,
                    jitter=jitter,
                )
        except ExceptionGroup as exc:
            exc_msg = "Failed fetching data from page(s)."
            raise FetchError(exc_msg) from exc

        keys = map(key_builder, zip(*key_columns, strict=False))
        elements = [task.result() for task in tasks]
        return dict(zip(keys, elements, strict=True))
