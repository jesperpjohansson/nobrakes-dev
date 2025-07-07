"""Internal logic abstracted for testability."""

from __future__ import annotations

import importlib
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, get_args

from nobrakes._constants import FIRST_AVAILABLE_SEASON
from nobrakes._element_utils import (
    string as string_utils,
    table as table_utils,
    xpath as xpath_utils,
)
from nobrakes._session.utils import with_delay, with_jitter
from nobrakes.exceptions import ElementError, UnsupportedClientError
from nobrakes.typing import ETreeElement, Language, Tier
from nobrakes.typing._typing import (
    URL,
    PgDataLabel,
    PgFetchModuleProtocol,
    SupportedClient,
)

if TYPE_CHECKING:
    import asyncio
    from collections.abc import Callable, Iterable, Iterator, Mapping

    from nobrakes._session.base import SessionAdapter

_AVAILABLE_TIERS: Final[frozenset[Tier]] = frozenset(
    get_args(Tier.__value__),  # pylint: disable=no-member
)
_AVAILABLE_LANGUAGES: Final[frozenset[Language]] = frozenset(
    get_args(Language.__value__),  # pylint: disable=no-member
)


def validate_launch_args(
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

    if not seasons:
        exceptions.append(ValueError("'*seasons' is empty."))
    elif unavailable := [s for s in seasons if s < FIRST_AVAILABLE_SEASON]:
        exceptions.append(ValueError(f"Unavailable seasons: {unavailable}"))

    if tier not in _AVAILABLE_TIERS:
        exceptions.append(ValueError(f"Unavailable tier: {tier}"))

    if language not in _AVAILABLE_LANGUAGES:
        exceptions.append(ValueError(f"Unavailable language: {language}"))

    if exceptions:
        exc_msg = "Invalid launch arg(s)."
        raise ExceptionGroup(exc_msg, exceptions)


def create_nested_pg_tasks[T: PgDataLabel](
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


def get_filtered_column_data(
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


def session_adapter_factory(session: SupportedClient) -> SessionAdapter:
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

    adapter_module = importlib.import_module(f"nobrakes._session.adapters.{lib_name}")
    adapter_type: type[SessionAdapter] = getattr(adapter_module, adapter_name)
    return adapter_type(session)


def get_hyperlink_href(td_elem: ETreeElement) -> str:
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
