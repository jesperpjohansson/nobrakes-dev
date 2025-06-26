# pylint: disable=R0801
"""Logic for extracting data from scorecard pages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from nobrakes._api.typing import ETreeElement, ScorecardPgDataLabel
from nobrakes._models import HashableMapping, TagSignature
from nobrakes._scraper.pgfetch import extract_elements

if TYPE_CHECKING:
    from nobrakes._session.base import SessionAdapter
    from nobrakes._typing import URL, NamedTargetTags

from types import MappingProxyType


@dataclass
class _Config:
    target_tags: NamedTargetTags


_CONFIG: Final[_Config] = _Config(
    target_tags=HashableMapping(
        {
            "result": TagSignature(
                tag="div", attrs=MappingProxyType({"class": "floatLeft"})
            ),
            "attendance": TagSignature(tag="h3"),
            "scorecard": TagSignature(
                tag="table", attrs=MappingProxyType({"class": "rgMasterTable"})
            ),
        },
    ),
)


async def fetch[K: ScorecardPgDataLabel](
    session: SessionAdapter,
    url: URL,
    *data: K,
) -> dict[K, ETreeElement]:
    """Fetch scorecard page data."""
    elements = await extract_elements(session, url, _CONFIG.target_tags, *data)
    return dict(zip(data, elements, strict=True))
