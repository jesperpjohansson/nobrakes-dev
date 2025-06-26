# pylint: disable=R0801
"""Logic for extracting data from events pages."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import count
import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from nobrakes._api.typing import ETreeElement, EventsPgDataLabel
from nobrakes._models import TagSignature
from nobrakes._scraper.table_browser import TableBrowser
from nobrakes._typing import URL, TBTargetTags, TBXPaths, is_element
from nobrakes.exceptions import ElementError, TablePageLimitError

if TYPE_CHECKING:
    from nobrakes._session.base import SessionAdapter


@dataclass
class _Config:
    target_tags: TBTargetTags
    browser_xpaths: TBXPaths


_CONFIG: Final[_Config] = _Config(
    target_tags=TBTargetTags(
        viewstate=TagSignature(
            tag="input", attrs=MappingProxyType({"id": "__VIEWSTATE"})
        ),
        table=TagSignature(
            tag="table", attrs=MappingProxyType({"class": "rgMasterTable"})
        ),
    ),
    browser_xpaths=TBXPaths(
        pagination='.//td[@class="rgPagerCell NextPrevAndNumeric"]',
        current_page='string(.//a[@class="rgCurrentPage"]/span)',
        last_visible_page='string(.//div[@class="rgWrap rgNumPart"]//a[last()]/span)',
        eventtarget='string(.//input[@class="rgPageNext"]/@name)',
    ),
)


async def fetch[K: EventsPgDataLabel](
    session: SessionAdapter,
    url: URL,
    *data: K,
    pagesize: int = 50,
    pagelimit: int = 10,
) -> dict[K, ETreeElement]:
    """Fetch competition page data."""
    # Replace pagesize parameter. Pagesize defaults to 10 if '”' is not removed.
    url = URL(re.sub("&pagesize=[125]0”?", f"&pagesize={pagesize}", url))

    browser = await TableBrowser(
        session,
        url,
        target_tags=_CONFIG.target_tags,
        xpaths=_CONFIG.browser_xpaths,
    ).launch()

    rows: list[ETreeElement] = []
    for i in count():
        if not i < pagelimit:
            exc_msg = f"Page limit ({pagelimit}) exceeded."
            raise TablePageLimitError(exc_msg)

        table = browser.table
        tbody = table.find("./tbody")
        if not is_element(tbody):
            exc_msg = "<table> is missing <tbody>."
            raise ElementError(exc_msg)

        rows.extend(tbody)
        tbody.clear()

        if browser.has_pagination and not browser.on_last_page:
            await browser.next_page()
        else:
            tbody.extend(rows)
            break

    return {data[0]: table}
