"""
Exceptions used throughout the `nobrakes` library.

All exceptions inherit from the base `NoBrakesError` class.

Exception Hierarchy
-------------------

NoBrakesError
├── ScraperError
│   └── UnsupportedClientError
├── FetchError
│   └── TablePageLimitError
└── ElementError
"""

__all__ = [
    "ElementError",
    "FetchError",
    "NoBrakesError",
    "ScraperError",
    "TablePageLimitError",
    "UnsupportedClientError",
]

# ≡≡≡ Base ≡≡≡


class NoBrakesError(Exception):
    """Base class for all library specific exceptions."""


# ≡≡≡ Scraper ≡≡≡


class ScraperError(NoBrakesError):
    """Exceptions caused by incorrect usage of `nobrakes.SVEMOScraper`."""


class UnsupportedClientError(ScraperError):
    """Raised when a client not supported by `nobrakes.SVEMOScraper` scraper is used."""


# ≡≡≡ Fetch ≡≡≡


class FetchError(NoBrakesError):
    """Exceptions encountered while fetching pages."""


class TablePageLimitError(FetchError):
    """Raised when the maximum number of table pages to fetch has been exceeded."""


# ≡≡≡ HTML Element ≡≡≡


class ElementError(NoBrakesError):
    """Base class for exceptions arising while processing HTML markup."""
