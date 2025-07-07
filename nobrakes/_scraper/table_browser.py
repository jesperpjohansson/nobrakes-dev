"""Implements a browser for ASP.NET Web Forms-style paginated HTML tables."""

from __future__ import annotations

from copy import deepcopy
from functools import wraps
from typing import TYPE_CHECKING, Concatenate, Literal, Self, TypedDict, cast

from nobrakes._accumulator import ElementAccumulator
from nobrakes._element_utils import xpath
from nobrakes.exceptions import ElementError
from nobrakes.typing._typing import URL, TBTargetTags, TBXPaths, is_element

if TYPE_CHECKING:
    from collections.abc import Callable

    from nobrakes._session.base import ResponseAdapter, SessionAdapter
    from nobrakes.typing import ETreeElement


class _ButtonTexts(TypedDict):
    """XPaths required by the table browser."""

    current_page: str
    last_visible_page: str


def _ensure_launched[T: TableBrowser, **P, R](
    func: Callable[Concatenate[T, P], R],
) -> Callable[Concatenate[T, P], R]:
    """Raise `RuntimeError` if the instance has not been launched."""

    @wraps(func)
    def wrapper(self: T, *args: P.args, **kwargs: P.kwargs) -> R:
        if not self._launched:
            exc_msg = "Method 'launch()' has not been called."
            raise RuntimeError(exc_msg)

        return func(self, *args, **kwargs)

    return cast("Callable[Concatenate[T, P], R]", wrapper)


def _require_pagination[T: TableBrowser, **P, R](
    func: Callable[Concatenate[T, P], R],
) -> Callable[Concatenate[T, P], R]:
    """Raise `ElementError` if pagination controls are missing from the parsed table."""

    @wraps(func)
    def wrapper(self: T, *args: P.args, **kwargs: P.kwargs) -> R:
        if self._pagination is None:  # pylint: disable=protected-access
            exc_msg = "Table has no pagination."
            raise ElementError(exc_msg)

        return func(self, *args, **kwargs)

    return cast("Callable[Concatenate[T, P], R]", wrapper)


class TableBrowser:
    """
    HTML table browser for paginated table extraction.

    Parameters
    ----------
    session : SessionAdapter
        HTTP session adapter used to make requests.
    url : URL
        Target URL of the paginated table.
    target_tags : TBTargetTags
        Tag signatures used to identify the viewstate and table elements.
    xpaths : TBXPaths
        XPath expressions used to locate pagination controls and buttons.
    """

    def __init__(
        self,
        session: SessionAdapter,
        url: URL,
        target_tags: TBTargetTags,
        xpaths: TBXPaths,
    ) -> None:
        self.session = session
        self.url = url

        self.accumulator = ElementAccumulator(
            target_tags["viewstate"],
            target_tags["table"],
        )

        self.xpaths = xpaths

        self._table: ETreeElement | None = None
        self._pagination: ETreeElement | None = None
        self._viewstate: str | None = None

        self._button_texts = _ButtonTexts(current_page="", last_visible_page="")

        self._launched: bool = False

    async def _handle_response(self, response: ResponseAdapter) -> None:
        """Parse the HTTP response, extract key elements and update state."""
        response.raise_for_status()
        chunks = response.iter_chunks()
        elements = await self.accumulator.aiter_feed(chunks)

        raise_exc = [False, False]
        match len(elements):
            case 0:
                raise_exc[0] = True
                raise_exc[1] = True
            case 1:
                i = int(elements[0].tag == "table")
                j = -1 * (i - 1)
                raise_exc[i] = not is_element(elements[0])
                raise_exc[j] = True
            case 2:
                raise_exc[0] = not is_element(elements[0])
                raise_exc[1] = not is_element(elements[1])

        if any(raise_exc):
            msgs = (
                "Input element containing viewstate.",
                "Entire table.",
                "Table footer.",
            )

            exc_group = ExceptionGroup(
                "Unable to browse table.",
                [
                    ElementError(exc_msg)
                    for true, exc_msg in zip(raise_exc, msgs, strict=False)
                    if true
                ],
            )
            exc_group.add_note(f"URL: {self.url}")
            raise exc_group

        input_elem, self._table = elements
        if val := input_elem.get("value"):
            self._viewstate = val
        else:
            exc_msg = "Missing viewstate value."
            raise ElementError(exc_msg)

        self._pagination = deepcopy(
            xpath.first_element_d(self._table, self.xpaths["pagination"]),
        )

        if (tfoot := self._table.find(".//tfoot")) is not None:
            self._table.remove(tfoot)

        self.accumulator.reset()

    async def launch(self) -> Self:
        """
        Fetch the first page.

        Raises
        ------
        ExceptionGroup
            If required HTML elements are missing or invalid.
        """
        async with self.session.get(self.url) as response:
            await self._handle_response(response)

        self._launched = True
        return self

    @property
    @_ensure_launched
    def table(self) -> ETreeElement:
        """
        Return the current table.

        Raises
        ------
        RuntimeError
            If `launch()` has not been called.
        """
        return cast("ETreeElement", self._table)

    @property
    @_ensure_launched
    def has_pagination(self) -> bool:
        """
        Return `True` if the table has pagination controls.

        Raises
        ------
        RuntimeError
            If `launch()` has not been called.
        """
        return self._pagination is not None

    @_ensure_launched
    @_require_pagination
    def _extract_button_text(
        self,
        key: Literal["last_visible_page", "current_page"],
    ) -> str:
        text = xpath.string(cast("ETreeElement", self._pagination), self.xpaths[key])
        if not text:
            exc_msg = f"{key.replace('_', ' ').capitalize()} button text not found."
            raise ElementError(exc_msg)

        return text

    @property
    def current_page(self) -> str:
        """
        Return the current page number as a string.

        Raises
        ------
        RuntimeError
            If `launch()` has not been called.
        """
        k: Literal["current_page"] = "current_page"
        if not self._button_texts[k]:
            self._button_texts[k] = self._extract_button_text(k)

        return self._button_texts[k]

    @property
    def last_visible_page(self) -> str:
        """
        Return the last visible page number in the pagination control.

        Raises
        ------
        RuntimeError
            If `launch()` has not been called.
        """
        k: Literal["last_visible_page"] = "last_visible_page"
        if not self._button_texts[k]:
            self._button_texts[k] = self._extract_button_text(k)

        return self._button_texts[k]

    @property
    def on_last_page(self) -> bool:
        """
        Return `True` if the browser is currently on the last page.

        Raises
        ------
        RuntimeError
            If `launch()` has not been called.
        """
        return self.current_page == self.last_visible_page

    @_ensure_launched
    @_require_pagination
    async def next_page(self) -> None:
        """
        Navigate to the next page by submitting a POST request with form data.

        Raises
        ------
        RuntimeError
            If `launch()` has not been called.
        ElementError
            If required DOM elements are missing.
        """
        eventtarget = xpath.string(
            cast("ETreeElement", self._pagination),
            self.xpaths["eventtarget"],
        )
        if not eventtarget:
            exc_msg = "Eventtarget not found."
            raise ElementError(exc_msg)

        form_data = {"__EVENTTARGET": eventtarget, "__VIEWSTATE": self._viewstate}

        async with self.session.post(self.url, data=form_data) as response:
            await self._handle_response(response)

        self._button_texts["current_page"] = ""
        self._button_texts["last_visible_page"] = ""
