# nobrakes
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)]()
[![License](https://img.shields.io/badge/license-BSD%203--Clause-blue.svg)](https://github.com/jesperpjohansson/nobrakes-dev/blob/main/LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-100.0%25-brightgreen)](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/ci.yml)
[![CI](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/ci.yml)

A high-level user API for asynchronous fetching, parsing and transformation of Swedish speedway data sourced from [SVEMO](https://www.svemo.se/).

> [!NOTE]
> Although the API is functional, `nobrakes` is in its **development phase**; hence:
> - The API should not yet be considered stable.
> - Breaking changes may occur without prior notice or appropriate versioning.
> - Documentation may be incomplete or evolving.

> [!IMPORTANT]
> `nobrakes` is an independent project and **is not affiliated with, endorsed by, or
> sponsored by SVEMO**. This library provides an unofficial API for accessing publicly
> available speedway data from SVEMO's website for convenience. Use responsibly and
> respect SVEMO's terms of service.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Advanced Usage](#advanced-usage)
- [SVEMO Overview](#svemo-overview)
- [License](#license)

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
3. Install development dependencies and the package in editable mode:
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
    async with aiohttp.ClientSession() as session:

        scraper = SVEMOScraper(session) # Initialize the scraper with an aiohttp session

        seasons = (2023,) # Specify the season(s) to scrape

        # The launched scraper is configured to enable extraction of 
        # Bauhausligan (tier 1) data from season 2023 in English.
        await scraper.launch(*seasons, tier=1, language="en-us")

        # The attendance page hosts two extractable sections, a paragraph containing the
        # seasonal average attendance and a table containing event-specific attendance
        # figures. Here, only the paragraph is fetched.
        pg_data = await scraper.attendance("average", season=2023)
    
    # The page model transforms the parsed page data and extracts relevant information
    pg_model = pgmodel.Attendance.from_pgelements(pg_data)

    # Output the average attendance value
    print(f"Average Attendance 2023: {pg_model.average}")

    # Output the attendance table (None in this example, since only paragraph was fetched)
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
The `nobrakes` library natively supports two asynchronous HTTP clients,
`aiohttp.ClientSession` and `httpx.AsyncClient`. Support for additional asynchronous
HTTP clients can be implemented by subclassing the `SessionAdapter` and
`ResponseAdapter` base classes.


To ensure your custom session adapter will integrate smoothly with nobrakes'
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

    # Requests must be returned as asynchronous context managers to be
    # compatible with the internal infrastructure of the package.
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

## SVEMO Overview

This section outlines the structure of the SVEMO website and the types of data available for scraping.

### Page Hierarchy

Below is a tree structure that illustrates the hierarchy of pages from which navigates through and extracts data.

```plaintext
home
├── results
│   ├── events
│   │   ├── scorecard
│   │   ├── scorecard
│   │   └── ...
│   ├── standings
│   ├── teams
│   │   ├── squad
│   │   ├── squad
│   │   └── ...
│   ├── rider averages
│   └── attendance
├── results
└── ...
```

### Results Page

Data is extracted from various [results pages](https://www.svemo.se/vara-sportgrenar/start-speedway/resultat-speedway/resultat-bauhausligan-speedway?language=en-us), grouped by league and season. Each results page acts as a central hub, containing five tabs. Each tab displays data directly, links to subpages, or both.

![Tabs](/assets/images/tabs.jpg)

The table below maps the SVEMO tab names to their corresponding API equivalents.

<table style="border-collapse: collapse; width: 100%; max-width: 800px; margin: 1em 0; font-family: Arial, 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #222;">
  <tbody>
    <tr style="background-color: #f5f5f5;">
      <td style="font-weight: 600; padding: 8px 12px; border: 1px solid #ccc;">SVEMO Tab</td>
      <td style="padding: 8px 12px; border: 1px solid #ccc;">Matchresultat</td>
      <td style="padding: 8px 12px; border: 1px solid #ccc;">Serietabell</td>
      <td style="padding: 8px 12px; border: 1px solid #ccc;">Aktuella snitt</td>
      <td style="padding: 8px 12px; border: 1px solid #ccc;">Snittlista</td>
      <td style="padding: 8px 12px; border: 1px solid #ccc;">Publikstatistik</td>
    </tr>
    <tr style="background-color: #ffffff;">
      <td style="font-weight: 600; padding: 8px 12px; border: 1px solid #ccc;">API Equivalent</td>
      <td style="padding: 8px 12px; border: 1px solid #ccc;">Events</td>
      <td style="padding: 8px 12px; border: 1px solid #ccc;">Standings</td>
      <td style="padding: 8px 12px; border: 1px solid #ccc;">Teams</td>
      <td style="padding: 8px 12px; border: 1px solid #ccc;">Rider Averages</td>
      <td style="padding: 8px 12px; border: 1px solid #ccc;">Attendance</td>
    </tr>
  </tbody>
</table>

### Tab Overview

Each tab on the results page corresponds to a specific category of data.

#### Events

Lists basic match details and provides links to **Scorecard** pages with detailed match data.

![Scorecard Links](/assets/images/events-highlighted.jpg)

---
#### Standings

Displays the regular season table and play-off trees.

---
#### Teams

Lists team information and provides links to **Squad** pages containing rider data.

![Squad Links](/assets/images/teams-highlighted.jpg)

---
#### Rider Averages

Displays riders sorted by their average heat score in descending order.

---
#### Attendance

Provides a link to a standalone page that displays attendance figures.

## License

This project is licensed under the 3-Clause BSD License. See the [LICENSE](https://github.com/jesperpjohansson/nobrakes-dev/blob/main/LICENSE) file for details.
