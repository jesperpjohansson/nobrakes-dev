"""
Page element data structures.

See Also
--------
nobrakes._api.pgdata :
    Public re-export module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from nobrakes.typing import ETreeElement


class PgData(TypedDict, total=False):
    """Base class for data structures representing parsed SVEMO page data."""


class Attendance(PgData):
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


class RiderAverages(PgData):
    """
    Parsed rider averages page elements.

    Attributes
    ----------
    table : ETreeElement
        `<table>`. Lists rider averages.
    """

    table: ETreeElement


class Events(PgData):
    """
    Parsed events page elements.

    Attributes
    ----------
    table : ETreeElement
        `<table>`. Lists event information and links to scorecard and heat data pages.
    """

    table: ETreeElement


class Scorecard(PgData):
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


class Squad(PgData):
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


class Standings(PgData):
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


class Teams(PgData):
    """
    Parsed teams page elements.

    Attributes
    ----------
    table : ETreeElement
        `<table>`. Lists information on participating teams and links to squad pages.
    """

    table: ETreeElement
