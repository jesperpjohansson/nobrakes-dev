# pylint: disable=R0801
"""Logic for extracting data from rider averages pages."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from nobrakes._models import HashableMapping, TagSignature
from nobrakes._scraper.pgfetch import extract_elements
from nobrakes.typing import ETreeElement, RiderAveragesPgDataLabel

if TYPE_CHECKING:
    from nobrakes.client._base import SessionAdapter
    from nobrakes.typing._typing import URL, NamedTargetTags


@dataclass
class _Config:
    target_tags: NamedTargetTags


_CONFIG: Final[_Config] = _Config(
    target_tags=HashableMapping(
        {
            "table": TagSignature(
                tag="table", attrs=MappingProxyType({"class": "rgMasterTable"})
            )
        },
    ),
)


async def fetch[K: RiderAveragesPgDataLabel](
    session: SessionAdapter,
    url: URL,
    *data: K,
) -> dict[K, ETreeElement]:
    """Fetch rider averages page data."""
    return await extract_elements(session, url, _CONFIG.target_tags, *data)
