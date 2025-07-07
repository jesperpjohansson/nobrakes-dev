# pylint: disable=R0801
"""
Typed dictionaries representing parsed HTML elements from SVEMO pages.

This module defines a set of `TypedDict` subclasses modeling the parsed data
returned by the methods of `nobrakes.SVEMOScraper`. The intended purpose of the models
is twofold:
    1. Act as structured typing aids, linking the output produced by
       `nobrakes.SVEMOScraper` with the data transformation models defined in
       `nobrakes.pgmodel`.
    2. Provide detailed information on the parsed data, facilitating the implementation
       of custom data transformations.

Classes
-------
PgElements : typing.TypedDict
    Base class for all page element dictionaries.

Attendance : PgElements
    Elements fetched from attendance pages.

RiderAverages : PgElements
    Elements fetched from rider averages pages.

Events : PgElements
    Elements fetched from events pages.

Scorecard : PgElements
    Elements fetched from scorecard pages.

Squad : PgElements
    Elements fetched from squad pages.

Standings : PgElements
    Elements fetched from standings pages.

Teams : PgElements
    Elements fetched from teams pages.

See Also
--------
nobrakes.SVEMOScraper :
    Produces the page data structures of this module.

nobrakes.pgmodel :
    Defines ready-to-use page data transformation models.
"""

from nobrakes.pgelements._pgelements import (
    Attendance,
    Events,
    PgElements,
    RiderAverages,
    Scorecard,
    Squad,
    Standings,
    Teams,
)

__all__ = [
    "Attendance",
    "Events",
    "PgElements",
    "RiderAverages",
    "Scorecard",
    "Squad",
    "Standings",
    "Teams",
]
