"""Utilities that enable type safe usage of lxml's `ETreeElement.xpath()`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nobrakes._typing import is_element_list, is_str, is_str_list
from nobrakes.exceptions import ElementError

if TYPE_CHECKING:
    from nobrakes._api.typing import ETreeElement


def element_list(elem: ETreeElement, xpath: str) -> list[ETreeElement]:
    """
    Evaluate `xpath` on `elem` and return a list of elements.

    Parameters
    ----------
    elem : ETreeElement
        The element on which to run the XPath query.
    xpath : str
        The XPath expression.

    Returns
    -------
    list[ETreeElement]
        List of elements matching the XPath.

    Raises
    ------
    ValueError
        If the XPath result is not a list of elements.
    """
    if is_element_list(x := elem.xpath(xpath)):
        return x

    exc_msg = "elem.xpath(xpath) did not return list[ETreeElement]."
    raise ValueError(exc_msg)


def string_list(elem: ETreeElement, xpath: str) -> list[str]:
    """
    Evaluate `xpath` on `elem` and return a list of strings.

    Parameters
    ----------
    elem : ETreeElement
        The element on which to run the XPath query.
    xpath : str
        The XPath expression.

    Returns
    -------
    list[str]
        List of strings matching the XPath.

    Raises
    ------
    ValueError
        If the XPath result is not a list of strings.
    """
    if is_str_list(x := elem.xpath(xpath)):
        return x

    exc_msg = "elem.xpath(xpath) did not return list[str]."
    raise ValueError(exc_msg)


def string(elem: ETreeElement, xpath: str) -> str:
    """
    Evaluate `xpath` on `elem` and return a single string.

    Parameters
    ----------
    elem : ETreeElement
        The element on which to run the XPath query.
    xpath : str
        The XPath expression.

    Returns
    -------
    str
        String matching the XPath.

    Raises
    ------
    ValueError
        If the XPath result is not a string.
    """
    if is_str(x := elem.xpath(xpath)):
        return x

    exc_msg = "elem.xpath(xpath) did not return str."
    raise ValueError(exc_msg)


def first_element_d(elem: ETreeElement, xpath: str) -> ETreeElement | None:
    """
    Return the first element matching `xpath`, or None if none found.

    Parameters
    ----------
    elem : ETreeElement
        The element on which to run the XPath query.
    xpath : str
        The XPath expression.

    Returns
    -------
    ETreeElement or None
        The first matching element, or None if no match.
    """
    return elements[0] if (elements := element_list(elem, xpath)) else None


def first_element_e(elem: ETreeElement, xpath: str) -> ETreeElement:
    """
    Return the first element matching `xpath`.

    Parameters
    ----------
    elem : ETreeElement
        The element on which to run the XPath query.
    xpath : str
        The XPath expression.

    Returns
    -------
    ETreeElement
        The first matching element.

    Raises
    ------
    ElementError
        If no elements match the XPath.
    """
    if (first_elem := first_element_d(elem, xpath)) is not None:
        return first_elem

    exc_msg = "No element found."
    raise ElementError(exc_msg)
