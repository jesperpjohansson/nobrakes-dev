# pylint: disable=R0801
"""Logic for extracting data from standings pages."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from nobrakes._api.typing import ETreeElement, StandingsPgDataLabel
from nobrakes._element_utils import xpath
from nobrakes._models import HashableMapping, TagSignature
from nobrakes._scraper.pgfetch import extract_elements

if TYPE_CHECKING:
    from collections.abc import Mapping

    from nobrakes._session.base import SessionAdapter
    from nobrakes._typing import URL, NamedTargetTags


@dataclass
class _Config:
    target_tags: NamedTargetTags
    xpath: Mapping[str, str]


_CONFIG: Final[_Config] = _Config(
    # The distinguishable <div> ancestors are targeted instead of the play-off
    # <table> elements, which all have identical tag signatures.
    target_tags=HashableMapping(
        {
            "po1": TagSignature(
                tag="div",
                attrs=MappingProxyType(
                    {"id": "ctl00_Body_Repeater1_ctl00_RadTreeList1"}
                ),
            ),
            "po2": TagSignature(
                tag="div",
                attrs=MappingProxyType(
                    {"id": "ctl00_Body_Repeater1_ctl01_RadTreeList1"}
                ),
            ),
            "po3": TagSignature(
                tag="div",
                attrs=MappingProxyType(
                    {"id": "ctl00_Body_Repeater1_ctl02_RadTreeList1"}
                ),
            ),
            "regular": TagSignature(
                tag="table", attrs=MappingProxyType({"class": "rgMasterTable"})
            ),
        },
    ),
    xpath={"table": "table"},
)


async def fetch[K: StandingsPgDataLabel](
    session: SessionAdapter,
    url: URL,
    *data: K,
) -> dict[K, ETreeElement]:
    """Fetch standings page data."""
    elements = list(await extract_elements(session, url, _CONFIG.target_tags, *data))

    for index in (i for i, s in enumerate(data) if s.startswith("po")):
        elements[index] = xpath.first_element_e(elements[index], "table")

    return dict(zip(data, elements, strict=True))
