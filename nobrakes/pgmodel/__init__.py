# pylint: disable=R0801
"""
Data transformation models for `nobrakes.SVEMOScraper` output.

This module provides a selection of `dataclass`-based models that transform the
HTML element data extracted by `nobrakes.SVEMOScraper` into structured, interpretable
and serializable objects. Each fetchable page has a corresponding model that
implements element-specific transformation methods.

Classes
-------
PgModel : abc.ABC
    Abstract base class for all transformation models.

Attendance : PgModel
    Transformed attendance page data.

RiderAverages : PgModel
    Transformed rider averages page data.

Events : PgModel
    Transformed events page data.

Scorecard : PgModel
    Transformed scorecard page data.

Squad : PgModel
    Transformed squad page data.

Standings : PgModel
    Transformed standings page data.

Teams : PgModel
    Transformed teams page data.

See Also
--------
nobrakes.SVEMOScraper
    Extracts HTML elements from SVEMO pages, producing the data structures
    found in `nobrakes.pgelements`.

nobrakes.pgelements
    Contains the HTML-element based data structures used as input to these models.
"""

from nobrakes.pgmodel._pgmodel import (
    Attendance,
    Events,
    PgModel,
    RiderAverages,
    Scorecard,
    Squad,
    Standings,
    Teams,
)

__all__ = [
    "Attendance",
    "Events",
    "PgModel",
    "RiderAverages",
    "Scorecard",
    "Squad",
    "Standings",
    "Teams",
]
