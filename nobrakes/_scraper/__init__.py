"""Subpackage dedicated to implementing `SVEMOScraper`."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from functools import wraps
import importlib
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Concatenate,
    Final,
    Literal,
    Self,
    cast,
    get_args,
    overload,
)

from nobrakes._constants import FIRST_AVAILABLE_SEASON, HOME_DOMAIN, TA_DOMAIN
from nobrakes._element_utils import (
    string,
    string as string_utils,
    table as table_utils,
    xpath as xpath_utils,
)
from nobrakes.client._base import SessionAdapter
from nobrakes.client._utils import with_delay, with_jitter
from nobrakes.exceptions import (
    ElementError,
    FetchError,
    ScraperError,
    TablePageLimitError,
    UnsupportedClientError,
)
from nobrakes.typing import Language, Tier
from nobrakes.typing._typing import (
    URL,
    PgCache,
    PgDataLabel,
    PgFetchModuleProtocol,
    SupportedClient,
    TabPgModuleLabel,
    URLCache,
    is_element,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Iterator, Mapping

    from nobrakes import pgelements
    from nobrakes.typing import (
        AttendancePgDataLabel,
        ETreeElement,
        EventsPgDataLabel,
        RiderAveragesPgDataLabel,
        ScorecardPgDataLabel,
        SquadPgDataLabel,
        StandingsPgDataLabel,
        SupportedClient,
        TeamsPgDataLabel,
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


_AVAILABLE_TIERS: Final[frozenset[Tier]] = frozenset(
    get_args(Tier.__value__),  # pylint: disable=no-member
)
_AVAILABLE_LANGUAGES: Final[frozenset[Language]] = frozenset(
    get_args(Language.__value__),  # pylint: disable=no-member
)


def _validate_launch_args(
    seasons: tuple[int, ...],
    tier: Tier,
    language: Language,
) -> None:
    """
    Validate arguments passed to `SVEMOScraper.launch()`.

    Checks that the seasons tuple is not empty and contains only supported seasons,
    and verifies that the provided tier and language are available.

    Raises
    ------
    ExceptionGroup
        If one or more input values are invalid, an ExceptionGroup containing
        all relevant exceptions is raised.
    """
    exceptions = []

    if unavailable_seasons := [s for s in seasons if s < FIRST_AVAILABLE_SEASON]:
        exceptions.append(ValueError(f"Unavailable seasons: {unavailable_seasons}"))

    if tier not in _AVAILABLE_TIERS:
        exceptions.append(ValueError(f"Unavailable tier: {tier}"))

    if language not in _AVAILABLE_LANGUAGES:
        exceptions.append(ValueError(f"Unavailable language: {language}"))

    if exceptions:
        exc_msg = "Invalid launch arg(s)."
        raise ExceptionGroup(exc_msg, exceptions)


def _create_nested_pg_tasks[T: PgDataLabel](
    *data: PgDataLabel,
    pg_module: PgFetchModuleProtocol[T],
    tg: asyncio.TaskGroup,
    session: SessionAdapter,
    urls: Iterable[URL],
    delay: float | None,
    jitter: tuple[float, float] | None,
) -> list[asyncio.Task[T]]:
    """
    Create and schedule asynchronous fetch tasks for nested pages.

    Parameters
    ----------
    *data : PgDataLabel
        Data labels specifying what to fetch from each page.
    pg_module : PgFetchModuleProtocol[T]
        The page fetch module providing a `fetch` coroutine.
    tg : asyncio.TaskGroup
        The task group to which the fetch tasks will be added.
    session : SessionAdapter
        The session adapter used to perform HTTP requests.
    urls : Iterable[URL]
        URLs of pages to fetch data from.
    delay : float | None
        Optional delay (in seconds) between task start times to stagger requests.
    jitter : tuple[float, float] | None
        Optional (min, max) jitter range (in seconds) to randomize task start times.

    Returns
    -------
    list[asyncio.Task[T]]
        List of asyncio tasks created and scheduled within the given task group.
    """
    tasks: list[asyncio.Task[T]] = []

    for i, url in enumerate(urls):
        coro = pg_module.fetch(session, url, *data)

        if jitter:
            coro = with_jitter(*jitter, coro=coro)

        if delay:
            coro = with_delay(i * delay, coro=coro)

        tasks.append(tg.create_task(coro))

    return tasks


def _filtered_column_data(
    table: ETreeElement,
    predicates: dict[int, Callable[[str], bool]],
    extractors: dict[int, Callable[[ETreeElement], str]],
) -> Iterator[list[str]]:
    """
    Extract and yield data columns from a filtered `<tbody>`.

    Applies predicates to filter rows of the table, then applies extractors
    to specific columns of the filtered rows to retrieve string data.

    Parameters
    ----------
    table : ETreeElement
        The `<table>` element containing the data.
    predicates : dict[int, Callable[[str], bool]]
        Mapping of column indices to predicates used to filter rows by cell text.
    extractors : dict[int, Callable[[ETreeElement], str]]
        Mapping of column indices to functions extracting string data from cells.

    Yields
    ------
    list[str]
        Lists of extracted strings for each specified column.

    Raises
    ------
    ElementError
        If the table element does not contain a `<tbody>` child.
    """
    if (tbody := table.find("./tbody")) is not None:
        subset = table_utils.filtered_tbody(tbody, predicates)
    else:
        exc_msg = "Expected child <tbody> is missing from <table>."
        raise ElementError(exc_msg)

    for i, f in extractors.items():
        yield list(map(f, table_utils.column(subset, i)))


_SESSION_ADAPTER_NAMES: Final[Mapping[tuple[str, str], str]] = MappingProxyType(
    {
        ("aiohttp", "ClientSession"): "AIOHTTPSessionAdapter",
        ("httpx", "AsyncClient"): "HTTPXSessionAdapter",
    },
)


def _session_adapter_factory(session: SupportedClient) -> SessionAdapter:
    """
    Return a `SessionAdapter` instance for the given HTTP client session.

    Parameters
    ----------
    session : SupportedClient
        Any of the following supported third-party clients:
        - `aiohttp.ClientSession`
        - `httpx.AsyncClient`

    Raises
    ------
    UnsupportedClientError
        If `session` is an unsupported client.
    """
    lib_name: str = session.__class__.__module__.split(".")[0]
    cls_name: str = session.__class__.__name__

    adapter_name: str | None = _SESSION_ADAPTER_NAMES.get((lib_name, cls_name))
    if adapter_name is None:
        exc_msg = f"'{cls_name}' from library '{lib_name}' is not a supported session."
        raise UnsupportedClientError(exc_msg)

    adapter_module = importlib.import_module(f"nobrakes.client._support.{lib_name}")
    adapter_type: type[SessionAdapter] = getattr(adapter_module, adapter_name)
    return adapter_type(session)


def _get_hyperlink_href(td_elem: ETreeElement) -> str:
    """
    Extract the href attribute from the first `<a>` element within `td_elem`.

    Parameters
    ----------
    td_elem : ETreeElement
        The `<td>` element expected to contain an `<a>` tag.

    Returns
    -------
    str
        The href value of the anchor tag inside the `<td>` element.

    Raises
    ------
    ElementError
        If the `<a>` element is not found or does not contain an href.
    """
    hyperlink = xpath_utils.first_element_e(td_elem, "./a")
    return string_utils.href_e(hyperlink)


class SVEMOScraper:
    """
    An asynchronous scraper for SVEMO speedway data.

    `SVEMOScraper` provides methods to fetch structured HTML data from various pages
    on the SVEMO website.

    Parameters
    ----------
    session : SupportedClient
        An instance of either a subclass of `nobrakes.clientAdapter` or one of
        the following supported third-party clients:

        - `aiohttp.ClientSession`
        - `httpx.AsyncClient`

    Raises
    ------
    UnsupportedClientError
        If the provided `session` is neither an instance of a subclass of
        `nobrakes.clientAdapter` nor an instance of a supported third-party client.

    Notes
    -----
    `SVEMOScraper` does **not** manage the lifecycle of the `session` instance.
    The caller is responsible for creating, managing, and closing the session.
    """

    def __init__(self, session: SupportedClient) -> None:
        self._launched = False
        self._url_cache: URLCache = {}
        self._pg_cache: PgCache = {}

        try:
            self._session: SessionAdapter = (
                session
                if isinstance(session, SessionAdapter)
                else _session_adapter_factory(session)
            )
        except UnsupportedClientError:  # noqa: TRY203
            raise  # Re-raise the exception to ensure cross-references work in API docs

    async def launch(
        self,
        season: int,
        *additional_seasons: int,
        tier: Tier = 1,
        language: Language = "sv-se",
    ) -> Self:
        """
        Launch the `SVEMOScraper` instance.

        Parameters
        ----------
        season, *additional_seasons : int
            Season(s) to enable scraping for. Valid values are from 2011 onwards.
        tier : Tier
            The league tier to scrape:

            - 1 : Bauhausligan/Elitserien
            - 2 : Allsvenskan.
        language : Language
            Language setting for the scraper:

            - 'sv-se' : Swedish
            - 'en-us' : English

        Returns
        -------
        Self
            A ready-to-use instance of `SVEMOScraper`.

        Raises
        ------
        ExceptionGroup
            If invalid arguments are passed.
        ScraperError
            If the `SVEMOScraper` instance has already been launched.
        FetchError
            If unable to fetch the URLs required for further scraping.
        """
        if self._launched:
            exc_msg = "The scraper has already been launched."
            raise ScraperError(exc_msg)

        seasons = (season, *additional_seasons)
        _validate_launch_args(seasons, tier, language)

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
        Fetch *events* page data.

        Parameters
        ----------
        season : int
            The season to fetch data for.
        cache : bool
            Whether or not to cache the fetched data.
        pagesize : int
            Number of rows per page, by default 50.
        pagelimit : int
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
        try:
            return await self._fetch_tab_pg_data(
                "table",
                pg="events",
                season=season,
                cache=cache,
                pagesize=pagesize,
                pagelimit=pagelimit,
            )
        except TablePageLimitError:  # noqa: TRY203 # pragma: no cover
            raise  # Re-raise the exception to ensure cross-references work in API docs

    async def standings(
        self,
        data: StandingsPgDataLabel,
        *additional_data: StandingsPgDataLabel,
        season: int,
    ) -> pgelements.Standings:
        """
        Fetch *standings* page data.

        Parameters
        ----------
        data, *additional_data : StandingsPgDataLabel
            Page data to extract.

            - 'po1' : Results from the finals.
            - 'po2' : Results from the semifinals, or equivalent.
            - 'po3' : Results from the semifinals, or equivalent.
            - 'regular' : The regular season table.
        season : int
            Target season.

        Returns
        -------
        pgelements.Standings
            Parsed page data.

        Raises
        ------
        ValueError
            If `season` was not passed when the session was launched.
        FetchError
            If the page data could not be fetched.

        Notes
        -----
        Due to changes to the play-off format, some pages will have less than
        three race off sections.

        """
        return await self._fetch_tab_pg_data(
            data, *additional_data, pg="standings", season=season
        )

    async def teams(self, *, season: int, cache: bool = False) -> pgelements.Teams:
        """
        Fetch *teams* page data.

        Parameters
        ----------
        season : int
            Target season.
        cache : bool
            Whether or not to cache the fetched data.

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
        Fetch *rider averages* page data.

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
        data: AttendancePgDataLabel,
        *additional_data: AttendancePgDataLabel,
        season: int,
    ) -> pgelements.Attendance:
        """
        Fetch *attendance* page data.

        Parameters
        ----------
        data, *additional_data : AttendancePgDataLabel
            Page data to extract.

            - 'average' : The average attendance figure.
            - 'table' : Attendance figures by event.
        season : int
            Target season.

        Returns
        -------
        pgelements.Attendance
            Parsed page data.

        Raises
        ------
        ValueError
            If `season` was not passed when the session was launched.
        FetchError
            If the page data could not be fetched.

        """
        return await self._fetch_tab_pg_data(
            data, *additional_data, pg="attendance", season=season
        )

    async def scorecards(
        self,
        data: ScorecardPgDataLabel,
        *additional_data: ScorecardPgDataLabel,
        season: int,
        date_query: Callable[[str], bool] | None = None,
        name_query: Callable[[str], bool] | None = None,
        delay: float | None = None,
        jitter: tuple[float, float] | None = None,
        **events_pg_kwargs,
    ) -> dict[tuple[str, str], pgelements.Scorecard]:
        """
        Fetch data from multiple *scorecard* pages.

        The pages are accessed through links found in the fourth column of an
        *events* page table.

        Parameters
        ----------
        data, *additional_data : ScorecardPgDataLabel
            Page data to extract.

            - 'result' : Team names and points.
            - 'attendance' : The attendance figure.
            - 'table' : A scorecard containing heat data.
        season : int
            Target season.
        date_query : Callable[[str], bool], optional
            A predicate function to filter *events* table rows based on first column.
            The input is a string in the format returned by the source site.
        name_query : Callable[[str], bool], optional
            A predicate function to filter *events* table rows based on second column.
            The input is a string in the format returned by the source site.
        delay : float, optional
            Delay applied before each fetch, in seconds.
        jitter : tuple[float, float], optional
            Tuple representing random jitter range (min, max) applied before
            each fetch, in seconds.
        **events_pg_kwargs : Any
            Keyword arguments forwarded to `events()`. Redundant when a cached
            table is used.

        Returns
        -------
        dict[tuple[str, str], pgelements.Scorecard]
            Mapping of (date, name) to their parsed scorecard data.

        Raises
        ------
        ValueError
            If `season` was not passed when the session was launched.
        FetchError
            If the *events* page data could not be fetched.
            If data from one or more scorecard pages could not be fetched.

        """
        return await self._fetch_nested_pg_data(
            data,
            *additional_data,
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
                        _get_hyperlink_href,
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
        data: SquadPgDataLabel,
        *additional_data: SquadPgDataLabel,
        season: int,
        team_query: Callable[[str], bool] | None = None,
        delay: float | None = None,
        jitter: tuple[float, float] | None = None,
        **teams_pg_kwargs,
    ) -> dict[str, pgelements.Squad]:
        """
        Fetch data from multiple *squad* pages.

        The pages are accessed through links found in the fourth column of a
        *teams* page table.

        Parameters
        ----------
        data, *additional_data : SquadPgDataLabel
            Page data to extract.

            - 'riders' : A table containing information about non-guest riders.
            - 'guests' : A table containing information about guest riders.
        season : int
            Target season.
        team_query : Callable[[str], bool], optional
            A predicate function to filter *teams* table rows based on first column.
            The input is a string in the format returned by the source site.
        delay : float, optional
            Delay applied between each request, in seconds.
        jitter : tuple[float, float], optional
            Tuple representing random jitter range (min, max) applied before
            each fetch, in seconds.
        **teams_pg_kwargs : Any
            Keyword arguments forwarded to `teams()`. Redundant when a cached table
            is used.

        Returns
        -------
        dict[str, pgelements.Squad]]
            Mapping of team names to parsed squad data.

        Raises
        ------
        ValueError
            If `season` was not passed when the session was launched.
        FetchError
            If the *teams* page data could not be fetched.
            If data from one or more *squad* pages could not be fetched.

        """
        return await self._fetch_nested_pg_data(
            data,
            *additional_data,
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
                zip((1, 4), (string.stripped_text_e, _get_hyperlink_href), strict=False)
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
    async def _fetch_tab_pg_data(
        self,
        /,
        *data,
        pg,
        season,
        cache=False,
        **kwargs,
    ):
        """
        Fetch data from a tab-level page.

        Common mechanism for fetching data a page embedded in, or linked to in a
        *results* page tab.
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
            elements = await pg_module.fetch(
                self._session,
                url,
                *set(data),  # Drop duplicate labels
                **kwargs,
            )
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
        Fetch data from multiple pages accessed through an embedded page.

        Common mechanism for fetching data from pages that are only accessible through
        hyperlinks (`<a>`) found in a `<table>` contained by a page embedded in a
        *results* page tab.
        """
        table = (self._pg_cache.get(cache_key) or await fallback).get("table")

        if not is_element(table):
            exc_msg = f"Unexpected cached/fetched table type: {type(table)}."
            raise RuntimeError(exc_msg)

        *key_columns, href_column = await asyncio.to_thread(
            _filtered_column_data,
            table,
            col_predicates,
            col_extractors,
        )

        urls = (URL(f"{TA_DOMAIN}{href}") for href in href_column)

        try:
            async with asyncio.TaskGroup() as tg:
                tasks = _create_nested_pg_tasks(
                    *set(data),  # Drop duplicate labels
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
