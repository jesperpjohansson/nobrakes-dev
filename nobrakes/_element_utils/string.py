"""Utilities for extracting string values from HTML elements."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nobrakes.exceptions import ElementError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from nobrakes.typing import ETreeElement


def href(elem: ETreeElement) -> str | None:
    """
    Return the `href` attribute from `elem`.

    Parameters
    ----------
    elem : ETreeElement
        An HTML element.

    Returns
    -------
    str or None
        The `href` value, or `None` if missing.
    """
    return elem.get("href")


def href_e(elem: ETreeElement) -> str:
    """
    Return the `href` attribute from `elem`.

    Parameters
    ----------
    elem : ETreeElement
        An HTML element.

    Returns
    -------
    str
        The `href` value.

    Raises
    ------
    ElementError
        If `href` is missing.
    """
    if x := href(elem):
        return x

    exc_msg = "Element has no href attribute."
    raise ElementError(exc_msg)


def first_stripped_text(elem: ETreeElement) -> str:
    """
    Return the first non-empty stripped text from `elem` or its descendants.

    Parameters
    ----------
    elem : ETreeElement
        An HTML element.

    Returns
    -------
    str
        First stripped text, or an empty string if none found.
    """
    return next(iter_stripped_text(elem), "")


def first_stripped_text_e(elem: ETreeElement) -> str:
    """
    Return the first non-empty stripped text from `elem` or its descendants.

    Parameters
    ----------
    elem : ETreeElement
        An HTML element.

    Returns
    -------
    str
        First stripped text.

    Raises
    ------
    ElementError
        If no text content is found.
    """
    if text := first_stripped_text(elem):
        return text

    exc_msg = "Element contains no text."
    raise ElementError(exc_msg)


def stripped_text(elem: ETreeElement) -> str:
    """
    Return the stripped text content of `elem`.

    Parameters
    ----------
    elem : ETreeElement
        An HTML element.

    Returns
    -------
    str
        Stripped `text`, or an empty string if `text` is `None`.
    """
    if text := elem.text:
        return text.strip()
    return ""


def stripped_text_e(elem: ETreeElement) -> str:
    """
    Return the stripped text content of `elem`.

    Parameters
    ----------
    elem : ETreeElement
        An HTML element.

    Returns
    -------
    str
        Stripped `text` value.

    Raises
    ------
    ElementError
        If `text` is missing or empty after stripping.
    """
    if text := stripped_text(elem):
        return text

    exc_msg = "Element contains no text."
    raise ElementError(exc_msg)


def iter_stripped_text(elem: ETreeElement) -> Iterator[str]:
    """
    Yield non-empty, stripped text fragments from `elem` and its descendants.

    Parameters
    ----------
    elem : ETreeElement
        An HTML element.

    Yields
    ------
    str
        Stripped text fragments.
    """
    for t in map(str, elem.itertext()):
        if stripped := t.strip():
            yield stripped
