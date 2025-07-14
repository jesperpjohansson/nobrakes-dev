# Usage

## Basic
Below is a demostration of how to fetch and transform attendance data.

### Code
```python
import asyncio
import aiohttp

from nobrakes import SVEMOScraper, pgmodel

async def main():
    async with aiohttp.ClientSession() as session:
        
        # Initialize the scraper with an aiohttp session
        scraper = SVEMOScraper(session) 

        # Specify the season(s) to scrape
        seasons = (2023,) 

        # The launched scraper is configured to enable extraction of 
        # Bauhausligan (tier 1) data from season 2023 in English.
        await scraper.launch(*seasons, tier=1, language="en-us")

        # Parsed HTML
        pg_data = await scraper.attendance("average", season=2023)
    
    # The page model transforms the parsed page data and extracts relevant information
    pg_model = pgmodel.Attendance.from_pgelements(pg_data)

    # The attendance page hosts two extractable sections, a paragraph containing the
    # seasonal average attendance and a table containing event-specific attendance
    # figures. In this instance, only the paragraph was fetched.
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

## Advanced

### Extending Request Behavior
Custom request logic (concurrency limiting, logging, retry logic, etc.) can be achieved
by implementing a [custom session adapter](#custom-session-adapters), or by subclassing one of the native session
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

### Custom Session Adapters
The `nobrakes` library natively supports two asynchronous HTTP clients,
`aiohttp.ClientSession` and `httpx.AsyncClient`. Support for additional asynchronous
HTTP clients can be implemented by subclassing the `SessionAdapter` and
`ResponseAdapter` base classes.


To ensure your custom session adapter will integrate smoothly with nobrakes'
scraping infrastructure, keep the following in mind:

- The underlying HTTP session must automatically follow HTTP redirects.
- Upon awaiting `SVEMOScraper.launch()`, the library automatically adds or replaces
  the `accept` and `cookie` headers.
- The presence of the `ASP.NET_SessionId` cookie appears to cause significant slowdowns
  in request processing. To maintain optimal performance, it is recommended to avoid
  storing and sending this cookie.
  

