# nobrakes

![PyPI](https://img.shields.io/badge/PyPI-not%20available-red.svg)
![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.13-blue.svg)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://github.com/jesperpjohansson/nobrakes-dev/blob/main/LICENSE)
[![Build](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/build.yml/badge.svg)](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/build.yml)
[![Lint](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/lint.yml?branch=main)
[![Typecheck](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/typecheck.yml/badge.svg?branch=main)](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/typecheck.yml?branch=main)
[![Test](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/jesperpjohansson/nobrakes-dev/actions/workflows/test.yml?branch=main)
[![Coverage](https://coveralls.io/repos/github/jesperpjohansson/nobrakes-dev/badge.svg?branch=main)](https://coveralls.io/github/jesperpjohansson/nobrakes-dev?branch=main)


A high-level user API for asynchronous fetching, parsing and transformation of Swedish speedway data sourced from [SVEMO](https://www.svemo.se/).

> [!IMPORTANT]
> `nobrakes` is an independent project and **is not affiliated with, endorsed by, or
> sponsored by SVEMO**. This library provides an unofficial API for accessing publicly
> available speedway data from SVEMO's website for convenience. Use responsibly and
> respect SVEMO's terms of service.

## Table of Contents
- [License](#license)
- [Documentation](#documentation)
- [Installation](#installation)
- [Contributing](#contributing)

## License

This project is licensed under the BSD 3-Clause License. See [LICENSE](https://github.com/jesperpjohansson/nobrakes-dev/blob/main/LICENSE).

## Documentation

User-oriented documentation is available [here](https://nobrakes.readthedocs.io/en/latest/).

## Installation

```bash
# Clone the repository
git clone https://github.com/jesperpjohansson/nobrakes-dev.git
cd nobrakes-dev

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate    # Bash (Linux/macOS/Git Bash)
.\.venv\Scripts\activate.bat # Batch (Windows Command Prompt)
.\.venv\Scripts\Activate.ps1 # PowerShell

# Install development dependencies and the package in editable mode
pip install -e .[dev]
```

## Contributing

See [CONTRIBUTING.md](https://github.com/jesperpjohansson/nobrakes-dev/blob/main/CONTRIBUTING.md).