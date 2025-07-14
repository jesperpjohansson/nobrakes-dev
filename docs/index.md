# nobrakes
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue.svg)]()
[![License](https://img.shields.io/badge/license-BSD%203--Clause-blue.svg)](https://github.com/jesperpjohansson/nobrakes-dev/blob/main/LICENSE)

A high-level user API for asynchronous fetching, parsing and transformation of Swedish speedway data sourced from [SVEMO](https://www.svemo.se/).

!!! note
    Although the API is functional, `nobrakes` is still in its **development phase**; hence:

    - The API should not yet be considered stable.
    - Breaking changes may occur without prior notice or appropriate versioning.
    - Documentation may be incomplete and contain errors.
    - The package is not yet available on PyPI.

!!! warning
    `nobrakes` is an independent project and **is not affiliated with, endorsed by, or
    sponsored by SVEMO**. This library provides an unofficial API for accessing publicly available speedway data from SVEMO's website for convenience. Use responsibly and respect SVEMO's terms of service.
---

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

## License

This project is licensed under the [BSD 3-Clause License](https://github.com/jesperpjohansson/nobrakes-dev/blob/main/LICENSE).


## 📦 Installation

### PyPI
!!! note
    Not yet available.
```bash
pip install nobrakes
```

### Source

```bash
git clone https://github.com/jesperpjohansson/nobrakes-dev.git
cd nobrakes-dev
pip install .
```