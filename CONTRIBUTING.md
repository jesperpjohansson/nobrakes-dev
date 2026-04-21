# Contributing

> [!important]
> This `CONTIBUTING.md` is a draft. Everything is subject to change.
> This project does **not currently accept external contributions**.

Thank you for your interest in contributing to `nobrakes`! We welcome contributions from the community and appreciate your help to make this project better.

## Code of Conduct

This project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). **By participating in this project you agree to abide by its terms**.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub:

- Provide a clear and descriptive title.
- Describe the steps to reproduce the issue.
- Include any relevant code snippets or error messages.
- Mention your environment (Python version, OS, etc.).

## Submitting Pull Requests

1. **Create a new branch:**

    ```bash
    git checkout -b my-feature
    ```

2. **Make your changes**, ensuring you follow the project's [coding style](#quality-standards).

3. **Write tests** for your changes, if applicable.

4. **Run relevant quality checks** locally:

    ```bash
    python -m ruff format --check
    python -m ruff check
    python -m mypy
    python -m pytest
    ```

5. **Commit your changes** with a clear message:

    ```bash
    git commit -m "Add feature X with Y"
    ```

6. **Push your branch** and open a Pull Request on GitHub.

## Quality Standards

The repository contains Python package code in `nobrakes` and tests in `tests`.

All contributions must meet quality standards regarding [code](#code), [docstrings](#docstrings), [typing](#typing), and [testing](#testing). These are checked during CI. Configurations for the tools checking this can be found in `pyproject.toml`.

### Code

Code formatting and linting are [ruff](https://docs.astral.sh/ruff/)-based. As a starting point:

- Comply with [PEP8](https://peps.python.org/pep-0008/) but allow line lengths up to 88 characters.
- Run `python -m ruff format` to fix formatting issues.
- Run `python -m ruff format --check` to check formatting.
- Run `python -m ruff check` to check lint rule violations.

---
### Docstrings

Docstring linting is [ruff](https://docs.astral.sh/ruff/)-based. Run `python -m ruff check` to check for formatting issues and lint rule violations.

#### nobrakes

- Docstrings are mandatory for all code.
- Internal code demands less extensive documentation.
- Follow the [NumPy](https://numpydoc.readthedocs.io/en/latest/format.html) docstring convention.

#### tests

- Docstrings are optional, but welcomed.
- No docstring convention is enforced.

---
### Typing

Typechecking is [MyPy](https://mypy.readthedocs.io/en/stable/index.html)-based. Run `python -m mypy` to check for typing related errors.

#### nobrakes

- `nobrakes` is a [py.typed](https://peps.python.org/pep-0561/) package.
- All types are to be defined in [nobrakes/typing/_typing.py](nobrakes/typing/_typing.py).
- Types that are exposed in the public API **must** be re-exported in [nobrakes/typing/\_\_init\_\_.py](nobrakes/typing/__init__.py).

#### tests

Typing is **not** required.

---
### Testing

- The general rule is that unit tests are expected to be written for all code paths in `nobrakes` (100% coverage).
- Certain code paths may be exempted from the rule if there are valid reasons to do so.
- Tests are to be written using a framework consisting of [pytest](https://docs.pytest.org/en/stable/), [pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/latest/), and [unittest.mock](https://docs.python.org/3/library/unittest.mock.html).
- In addition to the unit tests, other tests such as integration tests are welcomed but not required.
- Run `python -m pytest` to test `nobrakes`.
- Run `python -m pytest --cov=nobrakes --cov-report=term-missing` to produce a coverage report.

## Need Help?

If you have questions or need guidance, feel free to open an issue or join discussions on GitHub.

Thanks again for contributing to `nobrakes`! Your help is greatly appreciated.
