# nobrakes
![PyPI](https://img.shields.io/badge/PyPI-not%20available-red.svg)
![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://github.com/jesperpjohansson/nobrakes-dev/blob/main/LICENSE)

A high-level user API for asynchronous fetching, parsing, and transforming Swedish speedway data sourced from [SVEMO](https://www.svemo.se/).

!!! note
    The API is functional, documented, and tested. However, `nobrakes` is still in the **late stages of development**; hence:
    
    - The package is not published on PyPI.
    - The API is not guaranteed to be stable.
    - Breaking changes may occur without prior notice or semantic versioning.
    - Documentation may be incomplete or contain inaccuracies.

!!! warning
    `nobrakes` is an independent project and **is not affiliated with, endorsed by, or
    sponsored by SVEMO**. This library provides an unofficial API for accessing publicly available speedway data from SVEMO's website for convenience. Use responsibly and respect SVEMO's terms of service.
---

## Features
- **Asynchronous Web Scraping:** Use `SVEMOScraper` to fetch and parse raw HTML content from the SVEMO website.
- **Structured Data Output:** Transform page data into native Python objects using page models provided in the `pgmodel` module.
- **Third-party HTTP Client Support:** Compatible with `aiohttp.ClientSession` and `httpx.AsyncClient`.
- **Customizable Request Handling:** Subclass session adapters to control concurrency, retries, logging, and more.

## Install

### PyPI

!!! note
    Not available at the moment.
```bash
pip install nobrakes
```

### Source

```bash
git clone https://github.com/jesperpjohansson/nobrakes-dev.git
cd nobrakes-dev
pip install .
```

## License

This project is licensed under the [BSD 3-Clause License](https://github.com/jesperpjohansson/nobrakes-dev/blob/main/LICENSE).