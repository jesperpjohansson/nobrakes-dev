"""
Page element data structures.

See Also
--------
nobrakes._api.pgelements :
    Public re-export module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from nobrakes.typing import ETreeElement


class PgElements(TypedDict, total=False):
    """Base class for data structures representing parsed SVEMO page data."""


class Attendance(PgElements):
    """
    Parsed attendance page elements.

    Attributes
    ----------
    average : ETreeElement
        `<p>`. Contains the average attendance figure.
    table : ETreeElement
        `<table>`. Lists event-specific attendance figures.
    """

    average: ETreeElement
    table: ETreeElement


class RiderAverages(PgElements):
    """
    Parsed rider averages page elements.

    Attributes
    ----------
    table : ETreeElement
        `<table>`. Lists rider averages.
    """

    table: ETreeElement


class Events(PgElements):
    """
    Parsed events page elements.

    Attributes
    ----------
    table : ETreeElement
        `<table>`. Lists event information and links to scorecard and heat data pages.
    """

    table: ETreeElement


class Scorecard(PgElements):
    """
    Parsed scorecard page elements.

    Attributes
    ----------
    result : ETreeElement
        `<div>`. Contains full team names and final scores.
    attendance : ETreeElement
        `<h3>`. Contains the attendance figure.
    scorecard : ETreeElement
        `<table>`. The scorecard.
    """

    result: ETreeElement
    attendance: ETreeElement
    scorecard: ETreeElement


class Squad(PgElements):
    """
    Parsed squad page elements.

    Attributes
    ----------
    riders : ETreeElement
        `<table>`. Lists information on riders.
    guests : ETreeElement
        `<table>`. Lists information on guest riders.
    """

    riders: ETreeElement
    guests: ETreeElement


class Standings(PgElements):
    """
    Parsed league standings page data.

    Attributes
    ----------
    po1 : ETreeElement
        `<table>`. The first play-off tree on the page.
    po2 : ETreeElement
        `<table>`. The second play-off tree on the page.
    po3 : ETreeElement
        `<table>`. The third play-off tree on the page.
    regular : ETreeElement
        `<table>`. The regular season table.
    """

    po1: ETreeElement
    po2: ETreeElement
    po3: ETreeElement
    regular: ETreeElement


class Teams(PgElements):
    """
    Parsed teams page elements.

    Attributes
    ----------
    table : ETreeElement
        `<table>`. Lists information on participating teams and links to squad pages.
    """

    table: ETreeElement
