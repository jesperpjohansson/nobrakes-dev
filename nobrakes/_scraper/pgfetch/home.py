# pylint: disable=R0801
"""Logic for extracting results page URLs from the home page."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from nobrakes._element_utils import xpath
from nobrakes._models import HashableMapping, TagSignature
from nobrakes._scraper.pgfetch import extract_elements
from nobrakes.exceptions import (
    ElementError,
    FetchError,
)
from nobrakes.typing._typing import URL, NamedTargetTags

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from nobrakes._session.base import SessionAdapter
    from nobrakes.typing import ETreeElement, Tier


@dataclass
class _Config:
    target_tags: NamedTargetTags
    tier_alias_records: Mapping[int, list[str]]
    xpath: Mapping[str, str]


_CONFIG: Final[_Config] = _Config(
    target_tags=HashableMapping(
        {
            "navbar": TagSignature(
                tag="div",
                attrs=MappingProxyType(
                    {"class": "mx-6 my-0 p-0 main-menu-offcanvas offcanvas-body"}
                ),
            ),
        },
    ),
    tier_alias_records={1: ["Bauhausligan", "Elitserien"], 2: ["Allsvenskan"]},
    xpath={
        # Relative to navbar
        "results": (
            './/a[@href="https://www.svemo.se/vara-sportgrenar/start-speedway/'
            'resultat-speedway/"]/../../../div/div'
        ),
        # Relative to results
        "previous_results": "./div/div/div/div",
        # Relative to a direct descendant of previous_results
        "previous_season": "string(./div/p/button/a)",
        # Relative to a direct descendant of previous_results
        "href_previous_season": 'string(./div/div/div/a[text()="{}"]/@href)',
        # Relative to results
        "href_current_season": 'string(./a[text()="Resultat {}"]/@href)',
    },
)


def _select_accordion(parent: ETreeElement, key: str) -> ETreeElement:
    try:
        return xpath.first_element_e(parent, _CONFIG.xpath[key])
    except ElementError as exc:
        exc_msg = "Failed selecting the {} accordion in the navigation bar."
        raise FetchError(exc_msg.format(key.replace("_", " "))) from exc


def _extract_previous_season_urls(
    previous_results: ETreeElement,
    tier_aliases: list[str],
) -> Iterator[tuple[int, URL]]:
    selectors = tuple(map(_CONFIG.xpath["href_previous_season"].format, tier_aliases))
    for elem in previous_results:
        season = xpath.string(elem, _CONFIG.xpath["previous_season"])
        if not season:
            exc_msg = "Failed to extract season from hyperlink text."
            raise ElementError(exc_msg)

        href = next((href for s in selectors if (href := xpath.string(elem, s))), None)
        if href is None:
            exc_msg = "Failed to extract URL from hyperlink href."
            raise ElementError(exc_msg)

        try:
            yield (int(season), URL(href))
        except ValueError as exc:
            exc_msg = f'Failed converting season "{season}" to integer.'
            raise ElementError(exc_msg) from exc


def _extract_current_season_url(
    results: ETreeElement,
    tier_aliases: list[str],
) -> URL:
    selectors = map(_CONFIG.xpath["href_current_season"].format, tier_aliases)
    if href := next((x for s in selectors if (x := xpath.string(results, s))), None):
        return URL(href)

    exc_msg = f"Could not select any href using tier aliases: {tier_aliases}"
    raise ElementError(exc_msg)


def _raise_if_unavailable(low_bound: int, high_bound: int, *seasons: int) -> None:
    unavailable = filter(lambda s: not low_bound <= s <= high_bound, seasons)
    if (s := next(unavailable, None)) is not None:
        exc = ValueError(f"Unavailable seasons: {sorted((s, *unavailable))}")
        exc.add_note(f"Available seasons: {low_bound} to {high_bound}")
        raise exc


async def fetch[K: int](
    session: SessionAdapter,
    url: URL,
    *seasons: K,
    tier: Tier,
) -> dict[K, URL]:
    """Fetch URLs to results pages."""
    iterator_ = await extract_elements(session, url, _CONFIG.target_tags, "navbar")
    navbar: ETreeElement = next(iterator_)
    results: ETreeElement = _select_accordion(navbar, "results")
    previous_results: ETreeElement = _select_accordion(results, "previous_results")

    try:
        tier_aliases: list[str] = _CONFIG.tier_alias_records[tier]
        items = _extract_previous_season_urls(previous_results, tier_aliases)
        urls: dict[int, URL] = dict(sorted(items))
    except Exception as exc:
        exc_msg = "Failed fetching URLs to result pages of previous seasons."
        raise FetchError(exc_msg) from exc

    current_season = max(urls) + 1
    _raise_if_unavailable(min(urls), current_season, *seasons)

    if current_season in seasons:
        try:
            urls[current_season] = _extract_current_season_url(results, tier_aliases)
        except Exception as exc:
            exc_msg = "Failed fetching the URL to the current season results page."
            raise FetchError(exc_msg) from exc

    return {season: urls[season] for season in seasons}
