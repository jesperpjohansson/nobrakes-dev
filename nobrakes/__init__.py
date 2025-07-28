# ruff: noqa: D400
"""
`nobrakes`

A high-level user API for asynchronous fetching, parsing, and transforming
Swedish speedway data sourced from SVEMO.

Classes
-------
SVEMOScraper
    An asynchronous scraper for speedway data sourced from SVEMO.

Modules & Subpackages
---------------------
client
    Tools for adapting third-party asynchronous HTTP libraries.
exceptions
    Exceptions used throughout the `nobrakes` library.
pgdata
    Typed dictionaries representing parsed HTML elements from SVEMO pages.
pgmodel
    Data transformation models for `nobrakes.SVEMOScraper` output.
typing
    Typing used throughout the `nobrakes` API.
"""

from nobrakes import client, pgdata, pgmodel, typing
from nobrakes._scraper import SVEMOScraper

__all__ = ["SVEMOScraper", "client", "pgdata", "pgmodel", "typing"]
