"""
Typing used throughout the `nobrakes` package.

nobrakes._api.typing :
    Public re-export module.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    NewType,
    Protocol,
    TypedDict,
    TypeGuard,
)

from lxml import etree

if TYPE_CHECKING:
    from nobrakes._api.pgelements import PgElements
    from nobrakes._models import HashableMapping, TagSignature
    from nobrakes._session.base import SessionAdapter

# ≡≡≡ API ≡≡≡
# Objects defined in this section are considered part of the user API and are
# to be re-exported in 'nobrakes._api.typing'.

# === Type Aliases ===

ETreeElement = etree._Element  # noqa: SLF001
type RowFuncs[R] = Sequence[Callable[[ETreeElement], R]]


# SVEMOScraper initialization and launch (kw)args.
type SupportedClient = Any
type Tier = Literal[1, 2]  # NOTE: Used in runtime code.
type Language = Literal["sv-se", "en-us"]  # NOTE: Used in runtime code.

# Labels for page data available for extraction.
type AttendancePgDataLabel = Literal["average", "table"]
type RiderAveragesPgDataLabel = Literal["table"]
type EventsPgDataLabel = Literal["table"]
type ScorecardPgDataLabel = Literal["result", "attendance", "scorecard"]
type SquadPgDataLabel = Literal["riders", "guests"]
type StandingsPgDataLabel = Literal["po1", "po2", "po3", "regular"]
type TeamsPgDataLabel = Literal["table"]
type PgDataLabel = (
    AttendancePgDataLabel
    | RiderAveragesPgDataLabel
    | EventsPgDataLabel
    | ScorecardPgDataLabel
    | SquadPgDataLabel
    | StandingsPgDataLabel
    | TeamsPgDataLabel
)

# ≡≡≡ INTERNAL ≡≡≡
# Objects defined in this section are NOT considered part of the user API and are NOT
# to be re-exported in 'nobrakes._api.typing'. Thus, an object defined in this section
# must NEVER be required by the end user.

# === New Types ===
URL = NewType("URL", str)

# === Type Aliases ===

# NOTE: Used in runtime code.
type TabPgModuleLabel = Literal[
    "events",
    "standings",
    "teams",
    "rider_averages",
    "attendance",
]

type TabPgKey = tuple[TabPgModuleLabel, int]
type URLCache = dict[TabPgKey, URL]
type PgCache = dict[TabPgKey, "PgElements"]

type NamedTargetTags = "HashableMapping[str, TagSignature]"

# === Protocols ===


class PgFetchModuleProtocol[T](Protocol):
    """Protocol for duck typing modules in `._scraper.pgfetch`."""

    async def fetch(
        self,
        session: SessionAdapter,
        url: URL,
        *data: object,
        **kwargs,
    ) -> T:
        """Fetch and parse HTML."""


# === Typed Dictionaries ===


class TBXPaths(TypedDict):
    """XPaths required by `._scraper.table_browser.TableBrowser`."""

    pagination: str
    current_page: str
    last_visible_page: str
    eventtarget: str


class TBTargetTags(TypedDict):
    """Tag signatures of elements required by `._scraper.table_browser.TableBrowser`."""

    viewstate: TagSignature
    table: TagSignature


# === Type Guards ===


def is_str_list(obj: object) -> TypeGuard[list[str]]:
    """Return True if obj is a `list` of `str`."""
    return is_list(obj) and all(isinstance(x, str) for x in obj)


def is_str_tuple(obj: object) -> TypeGuard[tuple[str, ...]]:
    """Return True if obj is a `tuple` of `str`."""
    return is_tuple(obj) and all(isinstance(x, str) for x in obj)


def is_element_list(obj: object) -> TypeGuard[list[ETreeElement]]:
    """Return True if obj is a `list` of `etree._Element`."""
    return is_list(obj) and all(isinstance(x, ETreeElement) for x in obj)


def is_str(obj: object) -> TypeGuard[str]:
    """Return `True` if `obj` is an instance of `str`."""
    return isinstance(obj, str)


def is_list(obj: object) -> TypeGuard[list]:
    """Return `True` if `obj` is an instance of `list`."""
    return isinstance(obj, list)


def is_tuple(obj: object) -> TypeGuard[tuple]:
    """Return `True` if `obj` is an instance of `tuple`."""
    return isinstance(obj, tuple)


def is_element(obj: object) -> TypeGuard[ETreeElement]:
    """Return `True` if `obj` is an instance of `etree._Element`."""
    return isinstance(obj, ETreeElement)
