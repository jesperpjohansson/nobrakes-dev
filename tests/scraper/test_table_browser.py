"""Tests for `nobrakes._scraper.table_browser`."""

from copy import deepcopy
import re
from unittest.mock import AsyncMock, Mock, patch

import pytest

from nobrakes._models import TagSignature
from nobrakes._scraper.table_browser import TableBrowser, TBTargetTags, TBXPaths
from nobrakes.exceptions import (
    ElementError,
)
from nobrakes.typing import ETreeElement
from tests.conftest import element_from_string

MODULEPATH = "nobrakes._scraper.table_browser"


@pytest.fixture
def browser_xpaths():
    return TBXPaths(
        pagination='.//td[@class="rgPagerCell NextPrevAndNumeric"]',
        current_page='string(.//a[@class="rgCurrentPage"]/span)',
        last_visible_page='string(.//div[@class="rgWrap rgNumPart"]//a[last()]/span)',
        eventtarget='string(.//input[@class="rgPageNext"]/@name)',
    )


@pytest.fixture
def browser_target_tags():
    return TBTargetTags(
        viewstate=TagSignature(tag="input", attrs={"id": "__VIEWSTATE"}),
        table=TagSignature(tag="table", attrs={"class": "rgMasterTable"}),
    )


@pytest.fixture
def viewstate():
    return element_from_string(
        """<input name="__VIEWSTATE" id="__VIEWSTATE" value="abc+pg1...xyz">"""
    )


@pytest.fixture
def viewstate_no_value(viewstate):
    copy_ = deepcopy(viewstate)
    copy_.attrib.pop("value")
    return copy_


@pytest.fixture
def next_page_button():
    return """<input name="eventtarget_value" class="rgPageNext">"""


TABLE_TEMPLATE = """
<table>
    <colgroup></colgroup>
    <thead></thead>
    <tfoot>
        <tr>
            <td>
                <caption></caption>
                <thead></thead>
                <tbody>
                    <tr>{pagination}</tr>
                </tbody>
            </td>
        </tr>
    </tfoot>
    <tbody></tbody>
</table>"""

PAGINATION_TEMPLATE = """
<td class="rgPagerCell NextPrevAndNumeric">
    <div class="rgWrap rgNumPart">
        {buttons}
    </div>
    <div class="rgWrap rgArrPart2">
        {next_page_button}
    </div>
</td>"""

VISIBLE_PAGE_TEMPLATE = """<a><span>{}</span></a>"""

CURRENT_PAGE_TEMPLATE = """<a class="rgCurrentPage"><span>{}</span></a>"""


def add_buttons(texts, current_page):
    html = []
    for t in texts:
        template = (
            CURRENT_PAGE_TEMPLATE
            if str(t) == str(current_page)
            else VISIBLE_PAGE_TEMPLATE
        )
        html.append(template.format(t))

    return "\n".join(html)


@pytest.fixture
def table_pg1(next_page_button):
    pagination = PAGINATION_TEMPLATE.format(
        buttons=add_buttons(["1", "2", "3", "..."], current_page="1"),
        next_page_button=next_page_button,
    )

    table = TABLE_TEMPLATE.format(pagination=pagination)
    return element_from_string(table)


@pytest.fixture
def table_pg4(next_page_button):
    pagination = PAGINATION_TEMPLATE.format(
        buttons=add_buttons(["...", "2", "3", "4"], current_page="4"),
        next_page_button=next_page_button,
    )

    table = TABLE_TEMPLATE.format(pagination=pagination)
    return element_from_string(table)


@pytest.fixture
def table_no_pagination():
    return element_from_string(TABLE_TEMPLATE.format(pagination=""))


@pytest.fixture
def table_no_pagination_buttons(table_pg1):
    copy_ = deepcopy(table_pg1)
    copy_.find(".//div[@class='rgWrap rgNumPart']").clear()
    return copy_


@pytest.fixture
def table_no_pagination_button_text(next_page_button):
    pagination = PAGINATION_TEMPLATE.format(
        buttons=add_buttons(["", "", "", ""], current_page=""),
        next_page_button=next_page_button,
    )

    table = TABLE_TEMPLATE.format(pagination=pagination)
    return element_from_string(table)


@pytest.fixture
def table_no_next_page_button():
    pagination = PAGINATION_TEMPLATE.format(
        buttons=add_buttons(["1", "2", "3", "4"], current_page="1"), next_page_button=""
    )

    table = TABLE_TEMPLATE.format(pagination=pagination)
    return element_from_string(table)


@pytest.fixture
def make_mock_accumulator(
    viewstate,
    viewstate_no_value,
    table_pg1,
    table_pg4,
    table_no_pagination,
    table_no_pagination_buttons,
    table_no_pagination_button_text,
    table_no_next_page_button,
):
    def _make(name):
        variants = {
            "pg1": [viewstate, table_pg1],
            "pg4": [viewstate, table_pg4],
            "no_viewstate": [table_pg1],
            "no_table": [viewstate],
            "no_viewstate_value": [viewstate_no_value, table_pg1],
            "empty": [],
            "no_pagination": [viewstate, table_no_pagination],
            "no_pagination_buttons": [viewstate, table_no_pagination_buttons],
            "no_pagination_button_text": [viewstate, table_no_pagination_button_text],
            "no_next_page_button": [viewstate, table_no_next_page_button],
        }
        mock_accumulator = Mock()
        mock_accumulator.aiter_feed = AsyncMock(return_value=deepcopy(variants[name]))
        return mock_accumulator

    return _make


@pytest.fixture
def browser_factory(mock_session, browser_xpaths, browser_target_tags):
    def _factory(mock_accumulator) -> TableBrowser:
        with patch(f"{MODULEPATH}.ElementAccumulator", return_value=mock_accumulator):
            return TableBrowser(
                mock_session,
                "http://example.com",
                target_tags=browser_target_tags,
                xpaths=browser_xpaths,
            )

    return _factory


@pytest.mark.asyncio
async def test_raises_if_missing_viewstate_element(
    browser_factory, make_mock_accumulator
):
    browser = browser_factory(make_mock_accumulator("no_viewstate"))
    with pytest.raises(
        ExceptionGroup, match=re.escape("Unable to browse table.")
    ) as exc_info:
        _ = await browser.launch()

    exceptions = exc_info.value.exceptions
    assert len(exceptions) == 1
    assert isinstance(exceptions[0], ElementError)
    assert exceptions[0].args[0] == "Input element containing viewstate."


@pytest.mark.asyncio
async def test_raises_if_missing_table_element(browser_factory, make_mock_accumulator):
    browser = browser_factory(make_mock_accumulator("no_table"))
    with pytest.raises(
        ExceptionGroup, match=re.escape("Unable to browse table.")
    ) as exc_info:
        _ = await browser.launch()

    exceptions = exc_info.value.exceptions
    assert len(exceptions) == 1
    assert isinstance(exceptions[0], ElementError)
    assert exceptions[0].args[0] == "Entire table."


@pytest.mark.asyncio
async def test_raises_if_missing_viewstate_and_table_elements(
    browser_factory, make_mock_accumulator
):
    browser = browser_factory(make_mock_accumulator("empty"))
    with pytest.raises(
        ExceptionGroup, match=re.escape("Unable to browse table.")
    ) as exc_info:
        _ = await browser.launch()

    exceptions = exc_info.value.exceptions
    assert len(exceptions) == 2
    assert all(isinstance(exc, ElementError) for exc in exceptions)
    assert exceptions[0].args[0] == "Input element containing viewstate."
    assert exceptions[1].args[0] == "Entire table."


@pytest.mark.asyncio
async def test_raises_if_missing_viewstate_value(
    browser_factory, make_mock_accumulator
):
    browser = browser_factory(make_mock_accumulator("no_viewstate_value"))
    with pytest.raises(ElementError, match=re.escape("Missing viewstate value.")):
        _ = await browser.launch()


@pytest.mark.parametrize("attrname", ["current_page", "last_visible_page", "next_page"])
def test_raises_if_not_launched(browser_factory, make_mock_accumulator, attrname):
    browser = browser_factory(make_mock_accumulator("pg1"))
    exc_msg = "Method 'launch()' has not been called."
    with pytest.raises(RuntimeError, match=re.escape(exc_msg)):
        getattr(browser, attrname).__call__()


@pytest.mark.parametrize("attrname", ["_extract_button_text", "next_page"])
@pytest.mark.asyncio
async def test_raises_if_missing_pagination(
    browser_factory, make_mock_accumulator, attrname
):
    browser = browser_factory(make_mock_accumulator("no_pagination"))
    await browser.launch()
    attr = getattr(browser, attrname)
    with pytest.raises(ElementError, match=re.escape("Table has no pagination.")):
        attr()


@pytest.mark.parametrize(
    ("attrname", "e_msg_substr"),
    [("current_page", "Current"), ("last_visible_page", "Last visible")],
)
@pytest.mark.asyncio
async def test_raises_if_missing_pagination_button_text(
    browser_factory, make_mock_accumulator, attrname, e_msg_substr
):
    browser = browser_factory(make_mock_accumulator("no_pagination_button_text"))
    await browser.launch()
    with pytest.raises(
        ElementError,
        match=re.escape(f"{e_msg_substr} page button text not found."),
    ):
        getattr(browser, attrname)


@pytest.mark.asyncio
async def test_raises_if_missing_eventtarget(browser_factory, make_mock_accumulator):
    browser = browser_factory(make_mock_accumulator("no_next_page_button"))
    await browser.launch()
    with pytest.raises(ElementError, match=re.escape("Eventtarget not found.")):
        await browser.next_page()


@pytest.mark.asyncio
async def testtable_browser_first_pg_state(browser_factory, make_mock_accumulator):
    mock_accumulator = make_mock_accumulator("pg1")
    browser = browser_factory(mock_accumulator)
    browser = await browser.launch()

    with patch(f"{MODULEPATH}.ElementAccumulator", return_value=mock_accumulator):
        assert isinstance(browser._table, ETreeElement)
        assert browser.has_pagination is True
        assert browser.current_page == "1"
        assert browser.last_visible_page == "..."
        assert browser.on_last_page is False


@pytest.mark.asyncio
async def testtable_browser_last_pg_state(browser_factory, make_mock_accumulator):
    mock_accumulator = make_mock_accumulator("pg4")
    browser = browser_factory(mock_accumulator)
    browser = await browser.launch()

    with patch(f"{MODULEPATH}.ElementAccumulator", return_value=mock_accumulator):
        assert isinstance(browser._table, ETreeElement)
        assert browser.has_pagination is True
        assert browser.current_page == "4"
        assert browser.last_visible_page == "4"
        assert browser.on_last_page is True


@pytest.mark.asyncio
async def test_next_page(make_mock_accumulator, browser_factory):
    mock_accumulator = make_mock_accumulator("pg1")
    browser = browser_factory(mock_accumulator)
    browser = await browser.launch()

    _ = browser.current_page
    _ = browser.last_visible_page

    assert all(x != "" for x in browser._button_texts.values())
    browser.accumulator = make_mock_accumulator("pg4")
    await browser.next_page()

    # ensure cache reset
    assert all(x == "" for x in browser._button_texts.values())

    # ensure new values are accurate
    assert browser.current_page == "4"
    assert browser.last_visible_page == "4"
