# pylint: disable=R0801
"""Logic for extracting URLs to the pages accessible via the tabs of a results page."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, TypedDict

from nobrakes._models import HashableMapping, TagSignature
from nobrakes._scraper.pgfetch import extract_elements
from nobrakes.exceptions import ElementError
from nobrakes.typing._typing import URL, NamedTargetTags, TabPgModuleLabel

if TYPE_CHECKING:
    from collections.abc import Iterator

    from nobrakes.session._base import SessionAdapter
    from nobrakes.typing import ETreeElement


class _XPathSelectors(TypedDict):
    tab_panels: str


@dataclass
class _Config:
    target_tags: NamedTargetTags
    xpath: _XPathSelectors


_CONFIG: Final[_Config] = _Config(
    target_tags=HashableMapping(
        {
            "tab_content": TagSignature(
                tag="div", attrs=MappingProxyType({"class": "tab-content"})
            )
        },
    ),
    xpath=_XPathSelectors(tab_panels="./*/*/*/*"),
)


async def fetch[K: TabPgModuleLabel](
    session: SessionAdapter,
    url: URL,
    *pg_names: K,
) -> dict[K, URL]:
    """Fetch URLs to the pages accessible via the tabs of a results page."""
    elements = await extract_elements(session, url, _CONFIG.target_tags, "tab_content")
    tab_content = elements["tab_content"]
    tab_panels: list[ETreeElement] = tab_content.findall(_CONFIG.xpath["tab_panels"])

    if len(tab_panels) != len(pg_names):
        exc_msg = f"Expected {len(pg_names)} tabs, found {len(tab_panels)}."
        raise ElementError(exc_msg)

    pg_urls: Iterator[URL] = (
        URL(elem.get("src") or elem.get("href") or "") for elem in tab_panels
    )

    output = dict(zip(pg_names, pg_urls, strict=False))

    if missing := {k: v for k, v in output.items() if v == ""}:
        exc_msg = f"Failed extracting URL(s) for pages: {sorted(missing.keys())}"
        raise ElementError(exc_msg)

    return output
