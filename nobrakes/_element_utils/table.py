"""Utilities for structured extraction and transformation of HTML <table> elements."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from lxml import etree

from nobrakes._element_utils import string
from nobrakes.exceptions import ElementError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping, Sequence

    from nobrakes.typing import ETreeElement


def column(tbody: ETreeElement, i: int) -> list[ETreeElement]:
    """
    Return a list of the `i`-th `<td>` element from each `<tr>` in `tbody`.

    Parameters
    ----------
    tbody : ETreeElement
        The `<tbody>` element containing rows.
    i : int
        1-based column index.

    Returns
    -------
    list[ETreeElement]
        List of `<td>` elements in the specified column.

    Raises
    ------
    IndexError
        If `i` is greater than the number of columns in any `<tr>`.
    """
    if column := tbody.findall(f"./tr/td[{i}]"):
        return column

    exc_msg = f"Index {i} is greater than the number of columns in <tbody>."
    raise IndexError(exc_msg)


def filtered_tbody(
    tbody: ETreeElement,
    predicates: Mapping[int, Callable[[str], bool]],
) -> ETreeElement:
    """
    Return a subset of `tbody`.

    Parameters
    ----------
    tbody : ETreeElement
        The `<tbody>` element to filter.
    predicates : Mapping[int, Callable[[str], bool]]
        Mapping of 1-based column indexes to predicate functions applied
        to the text content of the corresponding `<td>` elements.
        A row is included only if all predicates return True.

    Returns
    -------
    ETreeElement
        New `<tbody>` element with filtered rows.
    """
    indexes, funcs = zip(*predicates.items(), strict=False)

    columns = (column(tbody, i) for i in indexes)
    text_content_by_column = (map(string.first_stripped_text_e, c) for c in columns)

    column_wise_results = (
        map(f, t) for f, t in zip(funcs, text_content_by_column, strict=False)
    )
    row_wise_results = zip(*column_wise_results, strict=False)
    indexes_to_retain = (i for i, x in enumerate(map(all, row_wise_results)) if x)

    subset = etree.Element(tbody.tag)
    subset.extend(tuple(tbody[i] for i in indexes_to_retain))

    return subset


def apply(
    table: ETreeElement,
    thfuncs: Sequence[Callable[[ETreeElement], Any]],
    tdfuncs: Sequence[Callable[[ETreeElement], Any]],
) -> Iterator[list[Any]]:
    """
    Yield records extracted from an HTML `<table>`.

    Callables in `thfuncs` and `tdfuncs` are applied to `<th>` and `<td>` elements
    respectively, in each `<tr>` of `<thead>` and `<tbody>`. Each callable corresponds
    to a column position.

    Parameters
    ----------
    table : ETreeElement
        The `<table>` element.
    thfuncs : Sequence[Callable[[ETreeElement], Any]]
        Functions to apply to `<th>` elements.
    tdfuncs : Sequence[Callable[[ETreeElement], Any]]
        Functions to apply to `<td>` elements.

    Yields
    ------
    list[Any]
        Extracted record for each row.

    Raises
    ------
    ElementError
        If `<thead>` or `<tbody>` is missing.
    ValueError
        If lengths of `thfuncs` or `tdfuncs` do not match the number of columns.
    """
    thead, tbody = _select_table_children(table)

    for tr in thead:
        yield [f(th) for f, th in zip(thfuncs, tr, strict=True)]

    for tr in tbody:
        yield [f(td) for f, td in zip(tdfuncs, tr, strict=True)]


def stripped_text(table: ETreeElement) -> Iterator[list[str]]:
    """
    Yield records of stripped text content from an HTML `<table>`.

    Parameters
    ----------
    table : ETreeElement
        The `<table>` element.

    Yields
    ------
    list[str]
        List of stripped text for each row.

    Raises
    ------
    ElementError
        If `<thead>` or `<tbody>` is missing.
    """
    thead, tbody = _select_table_children(table)

    for tr in (*thead, *tbody):
        yield [string.stripped_text(x) for x in tr]


def first_stripped_text(table: ETreeElement) -> Iterator[list[str]]:
    """
    Yield records of the first stripped text content from an HTML `<table>`.

    "First stripped text" refers to the first non-empty text content found
    in a `<th>` or `<td>`, including descendants.

    Parameters
    ----------
    table : ETreeElement
        The `<table>` element.

    Yields
    ------
    list[str]
        List of first stripped texts for each row.

    Raises
    ------
    ElementError
        If `<thead>` or `<tbody>` is missing.
    """
    thead, tbody = _select_table_children(table)

    for tr in (*thead, *tbody):
        yield list(map(string.first_stripped_text, tr))


def _select_table_children(
    table: ETreeElement,
) -> tuple[ETreeElement, ETreeElement]:
    """
    Select `<thead>` and `<tbody>` elements from a `<table>`.

    Parameters
    ----------
    table : ETreeElement
        The `<table>` element.

    Returns
    -------
    tuple[ETreeElement, ETreeElement]
        The `<thead>` and `<tbody>` elements.

    Raises
    ------
    ElementError
        If either `<thead>` or `<tbody>` is missing.
    """
    thead = table.find("thead")
    tbody = table.find("tbody")

    if thead is None or tbody is None:
        child_is_none = zip(
            ("thead", "tbody"), (thead is None, tbody is None), strict=False
        )
        missing = (tag for tag, true in child_is_none if true)
        exc_msg = f"<table> is missing <{'> and <'.join(missing)}>."
        raise ElementError(exc_msg)

    return thead, tbody
