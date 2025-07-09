# nobrakes
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)]()
[![License](https://img.shields.io/badge/license-BSD%203--Clause-blue.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-100.0%25-brightgreen)]()
[![CI](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/ci.yml/badge.svg)](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/ci.yml)

A high-level user API for asynchronous fetching, parsing and transformation of Swedish speedway data sourced from [SVEMO](https://www.svemo.se/).

> [!IMPORTANT]
> `nobrakes` is an independent project and **is not affiliated with, endorsed by, or sponsored
> by SVEMO**. This library provides an unofficial
> API for accessing publicly available speedway data from SVEMO’s website for convenience and
> research purposes only. Use responsibly and respect SVEMO’s terms of service.

> [!IMPORTANT]
> `nobrakes` is currently in **beta**. This means:
> - The API and features are still under active development and may change without prior notice.
> - Some functionality might be incomplete or unstable.
> - There could be bugs or unexpected behavior, especially with edge cases or less common use 
    patterns.
> - Documentation may be incomplete or evolving.
> - Your feedback is highly valuable to help improve the package and fix issues.

## Table of Contents
- [License](#license)
- [Features](#features)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)
- [Advanced Usage](#advanced-usage)

## License

This project is licensed under the 3-Clause BSD License. See the LICENSE file for details.

## Dependencies

- Python >= 3.12.0
- lxml >= 5.3.0

## Features
- **Efficient Web Scraping:** Fetch and parse raw HTML content from the SVEMO website
  using the high-performance asynchronous `SVEMOScraper`.
- **Easy Data Transformation:** Transform `SVEMOScraper` output into structured,
  easy-to-use Python objects using the robust page models provided in the `pgmodel`
  module.
- **Third-party Asynchronous HTTP Client Support:** Built-in support for
  `aiohttp.ClientSession` and `httpx.AsyncClient`.
- **Customizable and Extensible:** Easily extend or customize HTTP session behavior 
  (concurrency control, logging, retry logic, etc.) by implementing your own session
  adapters, or subclassing native ones.

## Installation
### User

The package is not yet available on PyPI.

### Developer

1. Clone the repository:
    ```bash
    git clone https://github.com/myname/nobrakes.git
    cd nobrakes
    ```
2. Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    # On Unix or macOS:
    source .venv/bin/activate
    # On Windows (PowerShell):
    .\.venv\Scripts\Activate.ps1
    # On Windows (cmd):
    .\.venv\Scripts\activate.bat
    ```
3. Install development dependencies (including an editable install):
    ```bash
    pip install -e .[dev]
    ```

## Usage
Here's a basic usage example demonstrating how to fetch and transform data.

### Code
```python
import asyncio
import aiohttp

from nobrakes import SVEMOScraper, pgmodel

async def main():
    seasons = (2023,)
    async with aiohttp.ClientSession() as session:
        scraper = SVEMOScraper(session)

        # The scraper is configured to extract Bauhausligan 2023 data in English.
        await scraper.launch(*seasons, tier=1, language="en-us")

        # The attendance page hosts two extractable sections, a paragraph containing the
        # seasonal average attendance and a table containing event-specific attendance
        # figures. Here, only the paragraph is fetched.
        pg_data = await scraper.attendance("average", season=2023)
    
    # The page model transforms the parsed page data and extracts relevant information.
    pg_model = pgmodel.Attendance.from_pgelements(pg_data)

    print(f"Average Attendance 2023: {pg_model.average}")
    print(f"Attendance Table 2023: {pg_model.table}")

if __name__ == "__main__":
    asyncio.run(main())
```
### Output
```
Average Attendance 2023: 2448
Attendance Table 2023: None
```

## Advanced Usage

### Custom Session Adapters
The nobrakes library natively supports two asynchronous HTTP clients,
`aiohttp.ClientSession` and `httpx.AsyncClient`. Support for additional asynchronous
HTTP clients can be implemented by subclassing the `SessionAdapter` and
`ResponseAdapter` base classes.


To ensure your custom session adapter will integrate smoothly with nobrakes’
scraping infrastructure, keep the following in mind:
- The underlying HTTP session **must** automatically follow HTTP redirects.
- Upon awaiting `SVEMOScraper.launch()`, the library automatically adds or replaces
  the `accept` and `cookie` headers.
- The presence of the `ASP.NET_SessionId` cookie appears to cause significant slowdowns
  in request processing. To maintain optimal performance, it is recommended to avoid
  storing and sending this cookie.
  

### Extending Request Behavior
Custom request logic (concurrency limiting, logging, retry logic, etc.) can be achieved
by implementing a custom session adapter, or by subclassing one of the native session
adapters (`AIOHTTPSessionAdapter` and `HTTPXSessionAdapter`) and overriding its request
method.

Here is an example that demonstrates adding concurrency control using
`asyncio.Semaphore` by subclassing `AIOHTTPSessionAdapter` and overriding its
request method:
```python
import asyncio
from contextlib import asynccontextmanager

import aiohttp

from nobrakes import pgmodel, SVEMOScraper, AIOHTTPSessionAdapter

class MyAdapter(AIOHTTPSessionAdapter):

    def __init__(self, session, semaphore):
        self.semaphore = semaphore
        super().__init__(session)

    def request(self, method: str, url: str, **kwargs):
        @asynccontextmanager
        async def acm():
            async with (
                self.semaphore,
                AIOHTTPSessionAdapter.request(self, method, url, **kwargs) as response,
            ):
                yield response

        return acm()

async def main():
    async with aiohttp.ClientSession() as session:
        adapter = MyAdapter(session, asyncio.Semaphore(10))
        scraper = SVEMOScraper(adapter)
        # And so on...

if __name__ == "__main__":
    asyncio.run(main())
```
