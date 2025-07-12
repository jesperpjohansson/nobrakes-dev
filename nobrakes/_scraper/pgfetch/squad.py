# pylint: disable=R0801
"""Logic for extracting data from squad pages."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from nobrakes._element_utils import xpath
from nobrakes._models import HashableMapping, TagSignature
from nobrakes._scraper.pgfetch import extract_elements
from nobrakes.typing import ETreeElement, SquadPgDataLabel

if TYPE_CHECKING:
    from collections.abc import Mapping

    from nobrakes.session._base import SessionAdapter
    from nobrakes.typing._typing import URL, NamedTargetTags


@dataclass
class _Config:
    target_tags: NamedTargetTags
    xpath: Mapping[str, str]


_CONFIG: Final[_Config] = _Config(
    # The distinguishable <div> ancestors are targeted instead of the
    # <table> elements, which both have identical tag signatures.
    target_tags=HashableMapping(
        {
            "riders": TagSignature(
                tag="div", attrs=MappingProxyType({"id": "ctl00_Body_RadGrid1"})
            ),
            "guests": TagSignature(
                tag="div", attrs=MappingProxyType({"id": "ctl00_Body_RadGrid2"})
            ),
        },
    ),
    xpath={"table": "table"},
)


async def fetch[K: SquadPgDataLabel](
    session: SessionAdapter,
    url: URL,
    *data: K,
) -> dict[K, ETreeElement]:
    """Fetch squad page data."""
    elements = await extract_elements(session, url, _CONFIG.target_tags, *data)
    tables = (xpath.first_element_e(e, _CONFIG.xpath["table"]) for e in elements)
    return dict(zip(data, tables, strict=True))
